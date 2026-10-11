import json
from pathlib import Path

import numpy as np

from member3_analysis.mongodb.connection import get_database
from member3_analysis.mongodb.config import RIVER_COLLECTION


OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def analyse_rivers():
    """Analyse historical river-level observations in MongoDB."""

    client, db = get_database()

    try:
        collection = db[RIVER_COLLECTION]

        # District-level statistics
        district_pipeline = [
            {
                "$group": {
                    "_id": "$district",
                    "average_water_level": {
                        "$avg": "$average_water_level"
                    },
                    "maximum_water_level": {
                        "$max": "$maximum_water_level"
                    },
                    "minimum_water_level": {
                        "$min": "$minimum_water_level"
                    },
                    "records": {"$sum": 1},
                    "stations": {"$addToSet": "$station"},
                }
            },
            {"$sort": {"average_water_level": -1}},
        ]

        districts = list(collection.aggregate(district_pipeline))

        # Station-level statistics
        station_pipeline = [
            {
                "$group": {
                    "_id": {
                        "station": "$station",
                        "district": "$district",
                    },
                    "average_water_level": {
                        "$avg": "$average_water_level"
                    },
                    "maximum_water_level": {
                        "$max": "$maximum_water_level"
                    },
                    "minimum_water_level": {
                        "$min": "$minimum_water_level"
                    },
                    "records": {"$sum": 1},
                }
            },
            {"$sort": {"maximum_water_level": -1}},
        ]

        stations = list(collection.aggregate(station_pipeline))

        # Calculate a relative statistical threshold.
        # This is NOT an official flood-warning level.
        maximums = [
            item["maximum_water_level"]
            for item in stations
            if item.get("maximum_water_level") is not None
        ]

        threshold = (
            float(np.percentile(maximums, 95))
            if maximums
            else None
        )

        for station in stations:
            maximum = station.get("maximum_water_level")

            station["relative_level_flag"] = (
                "HIGH_RELATIVE_TO_DATA"
                if threshold is not None
                and maximum is not None
                and maximum >= threshold
                else "BELOW_DATA_THRESHOLD"
            )

        # Make the results JSON serializable.
        for district in districts:
            district["district"] = district.pop("_id")
            district["station_count"] = len(district["stations"])
            district["stations"] = sorted(district["stations"])

        for station in stations:
            station["station"] = station["_id"]["station"]
            station["district"] = station["_id"]["district"]
            del station["_id"]

        report = {
            "analysis": "Historical river-level analysis",
            "total_records": collection.count_documents({}),
            "district_count": len(districts),
            "station_count": len(stations),
            "95th_percentile_of_station_maximums": threshold,
            "threshold_note": (
                "Relative statistical threshold, not an official "
                "flood-warning level."
            ),
            "district_summaries": districts,
            "station_summaries": stations,
            "stations_with_high_relative_levels": [
                station
                for station in stations
                if station["relative_level_flag"]
                == "HIGH_RELATIVE_TO_DATA"
            ],
        }

        return report

    finally:
        client.close()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = analyse_rivers()
    output_file = OUTPUT_DIR / "river_analysis.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, default=str)

    print("\n--- RIVER ANALYSIS ---")
    print(f"Records: {report['total_records']}")
    print(f"Districts: {report['district_count']}")
    print(f"Stations: {report['station_count']}")
    print(
        "Stations with high relative historical levels:",
        len(report["stations_with_high_relative_levels"]),
    )
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()