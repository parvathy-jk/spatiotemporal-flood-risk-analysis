import json
from pathlib import Path

from member3_analysis.analysis.river_analysis import analyse_rivers
from member3_analysis.analysis.rainfall_analysis import analyse_rainfall
from member3_analysis.mongodb.connection import get_database
from member3_analysis.mongodb.config import RAINFALL_COLLECTION


OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def analyse_march_rainfall():
    """Analyse March 1–4, 2025 rainfall separately from other periods."""
    client, db = get_database()

    try:
        pipeline = [
            {
                "$match": {
                    "date": {
                        "$gte": "2025-03-01",
                        "$lte": "2025-03-04",
                    }
                }
            },
            {
                "$group": {
                    "_id": "$date",
                    "mean_rainfall_mm": {"$avg": "$rainfall_mm"},
                    "max_rainfall_mm": {"$max": "$rainfall_mm"},
                    "grid_cells": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        daily_results = list(
            db[RAINFALL_COLLECTION].aggregate(pipeline)
        )

        daily_summaries = [
            {
                "date": row["_id"],
                "mean_rainfall_mm": round(
                    row["mean_rainfall_mm"], 2
                ),
                "max_rainfall_mm": round(
                    row["max_rainfall_mm"], 2
                ),
                "grid_cells": row["grid_cells"],
                "reaches_100mm_screen": (
                    row["max_rainfall_mm"] >= 100
                ),
            }
            for row in daily_results
        ]

        return {
            "period": "2025-03-01 to 2025-03-04",
            "daily_summaries": daily_summaries,
            "days_found": len(daily_summaries),
            "days_reaching_100mm_screen": sum(
                item["reaches_100mm_screen"]
                for item in daily_summaries
            ),
            "assessment": (
                "Preliminary rainfall screening only. The 100 mm "
                "threshold is not an official flood-warning threshold."
            ),
        }

    finally:
        client.close()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Analysing historical river-level data...")
    river_report = analyse_rivers()

    print("Analysing rainfall and elevation data...")
    rainfall_report = analyse_rainfall()

    print("Screening March 2025 rainfall separately...")
    march_rainfall_report = analyse_march_rainfall()

    high_river_stations = (
        river_report["stations_with_high_relative_levels"]
    )

    heavy_rainfall_days = [
        item
        for item in rainfall_report["daily_summaries"]
        if item["heavy_rainfall_screen"]
    ]

    report = {
        "project": "Kerala Spatiotemporal Flood-Risk Analysis",
        "assessment_type": (
            "Preliminary, descriptive flood-risk screening"
        ),
        "river_analysis": {
            "records_analysed": river_report["total_records"],
            "districts_analysed": river_report["district_count"],
            "stations_analysed": river_report["station_count"],
            "relative_high_level_station_count": len(
                high_river_stations
            ),
            "relative_high_level_stations": high_river_stations,
            "district_summaries": river_report["district_summaries"],
        },
        "rainfall_analysis": {
            "records_analysed": rainfall_report["total_records"],
            "days_analysed": rainfall_report["days_analysed"],
            "daily_summaries": rainfall_report["daily_summaries"],
            "heavy_rainfall_screening_days": heavy_rainfall_days,
            "top_10_observations": (
                rainfall_report["top_10_rainfall_observations"]
            ),
        },
        "march_2025_rainfall_screening": march_rainfall_report,
        "elevation_data_quality": (
            rainfall_report["elevation_data_quality"]
        ),
        "interpretation": {
            "river_indicator": (
                "High relative levels identify station maxima near "
                "the upper end of this dataset. They do not establish "
                "official danger levels or prove that flooding occurred."
            ),
            "rainfall_indicator": (
                "The rainfall screening flag identifies days whose "
                "maximum grid-cell rainfall reaches the selected "
                "screening threshold."
            ),
            "march_rainfall_findings": (
                "March 1–4, 2025 rainfall was analysed separately. "
                "The daily maximum rainfall values were 42.60 mm, "
                "78.90 mm, 53.80 mm, and 7.30 mm, respectively. "
                "None reached the selected 100 mm screening threshold."
            ),
            "combined_risk_score": (
                "Not calculated because there are no same-day river "
                "observations for the March 1–4 rainfall period, and "
                "a validated combined scoring method has not been "
                "established."
            ),
        },
        "limitations": [
            (
                "Rainfall observations cover March 1–4, 2025 and "
                "August 1–4, 2025. River observations are available "
                "through March 10, 2025, but there are no river "
                "observations for March 1–4."
            ),
            (
                "The available data cannot establish a same-day "
                "rainfall-to-river-level relationship for March 1–4."
            ),
            (
                "The statistical river threshold is not an official "
                "flood-warning level."
            ),
            (
                "The rainfall screening threshold is not an official "
                "flood-warning threshold."
            ),
            (
                "Geographic coordinates in the rainfall output require "
                "verification before making location-specific map claims."
            ),
            (
                "The assessment is descriptive and has not been "
                "validated as a flood prediction model."
            ),
            (
                "Rainfall and elevation alone do not account for all "
                "flood-driving factors, such as drainage, soil "
                "saturation, land use, and river discharge."
            ),
        ],
    }

    output_file = OUTPUT_DIR / "combined_risk_assessment.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, default=str)

    print("\n--- COMBINED FLOOD-RISK ASSESSMENT ---")
    print(
        "River stations analysed:",
        report["river_analysis"]["stations_analysed"],
    )
    print(
        "Stations with high relative historical levels:",
        report["river_analysis"]["relative_high_level_station_count"],
    )
    print(
        "Rainfall days analysed across all periods:",
        report["rainfall_analysis"]["days_analysed"],
    )
    print(
        "Days reaching the rainfall screening threshold "
        "(all periods):",
        len(heavy_rainfall_days),
    )

    print("\n--- MARCH 2025 RAINFALL SCREENING ---")
    for item in march_rainfall_report["daily_summaries"]:
        print(
            f"{item['date']}: "
            f"mean={item['mean_rainfall_mm']:.2f} mm, "
            f"maximum={item['max_rainfall_mm']:.2f} mm, "
            f"cells={item['grid_cells']}"
        )

    print(
        "March days reaching the 100 mm screening threshold:",
        march_rainfall_report["days_reaching_100mm_screen"],
    )
    print("Combined risk score: Not calculated")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()