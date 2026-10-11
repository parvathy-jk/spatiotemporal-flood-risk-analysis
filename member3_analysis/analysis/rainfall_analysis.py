import json
from pathlib import Path

from member3_analysis.mongodb.connection import get_database
from member3_analysis.mongodb.config import RAINFALL_COLLECTION


OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Screening threshold only; this is not an official warning threshold.
HEAVY_RAINFALL_THRESHOLD_MM = 100.0


def analyse_rainfall():
    """Analyse rainfall and elevation information in MongoDB."""

    client, db = get_database()

    try:
        collection = db[RAINFALL_COLLECTION]

        # Daily rainfall statistics
        daily_pipeline = [
            {
                "$group": {
                    "_id": "$date",
                    "average_rainfall_mm": {
                        "$avg": "$rainfall_mm"
                    },
                    "maximum_rainfall_mm": {
                        "$max": "$rainfall_mm"
                    },
                    "minimum_rainfall_mm": {
                        "$min": "$rainfall_mm"
                    },
                    "grid_cells": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        daily_results = list(collection.aggregate(daily_pipeline))

        daily_summaries = []

        for item in daily_results:
            daily_summaries.append({
                "date": item["_id"],
                "average_rainfall_mm": item["average_rainfall_mm"],
                "maximum_rainfall_mm": item["maximum_rainfall_mm"],
                "minimum_rainfall_mm": item["minimum_rainfall_mm"],
                "grid_cells": item["grid_cells"],
                "heavy_rainfall_screen": (
                    item["maximum_rainfall_mm"]
                    >= HEAVY_RAINFALL_THRESHOLD_MM
                ),
            })

        # Top 10 grid-cell observations
        top_pipeline = [
            {
                "$project": {
                    "_id": 0,
                    "date": 1,
                    "grid_row": 1,
                    "grid_col": 1,
                    "rainfall_mm": 1,
                }
            },
            {"$sort": {"rainfall_mm": -1}},
            {"$limit": 10},
        ]

        top_observations = list(collection.aggregate(top_pipeline))

        # Elevation-data completeness
        total = collection.count_documents({})

        without_elevation = collection.count_documents({
            "elevation_mean": None
        })

        partial_elevation = collection.count_documents({
            "elevation_mean": {"$ne": None},
            "$expr": {
                "$lt": [
                    "$elevation_valid_pixels",
                    {
                        "$add": [
                            "$elevation_valid_pixels",
                            "$elevation_missing_pixels",
                        ]
                    },
                ]
            },
        })

        complete_elevation = (
            total - without_elevation - partial_elevation
        )

        report = {
            "analysis": "Rainfall and elevation analysis",
            "total_records": total,
            "days_analysed": len(daily_summaries),
            "heavy_rainfall_screening_threshold_mm": (
                HEAVY_RAINFALL_THRESHOLD_MM
            ),
            "threshold_note": (
                "Screening threshold only; not an official "
                "flood-warning threshold."
            ),
            "daily_summaries": daily_summaries,
            "top_10_rainfall_observations": top_observations,
            "elevation_data_quality": {
                "total_records": total,
                "without_elevation": without_elevation,
                "partial_elevation": partial_elevation,
                "complete_elevation": complete_elevation,
            },
        }

        return report

    finally:
        client.close()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = analyse_rainfall()
    output_file = OUTPUT_DIR / "rainfall_analysis.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, default=str)

    print("\n--- RAINFALL ANALYSIS ---")
    print(f"Records: {report['total_records']}")
    print(f"Days analysed: {report['days_analysed']}")
    print(
        "Observations in top 10:",
        len(report["top_10_rainfall_observations"]),
    )
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()