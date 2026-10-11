import json
from pathlib import Path

from member3_analysis.analysis.river_analysis import analyse_rivers
from member3_analysis.analysis.rainfall_analysis import analyse_rainfall


OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Analysing historical river-level data...")
    river_report = analyse_rivers()

    print("Analysing rainfall and elevation data...")
    rainfall_report = analyse_rainfall()

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
            "combined_risk_score": (
                "Not calculated because the available river and "
                "rainfall periods do not overlap, and a validated "
                "combined scoring method has not been established."
            ),
        },
        "limitations": [
            (
                "River data ends on 2025-03-10, while rainfall data "
                "covers 2025-08-01 through 2025-08-04."
            ),
            (
                "The datasets cannot currently establish a same-day "
                "rainfall-to-river-level relationship."
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
        "Rainfall days analysed:",
        report["rainfall_analysis"]["days_analysed"],
    )
    print(
        "Days reaching the rainfall screening threshold:",
        len(heavy_rainfall_days),
    )
    print("Combined risk score: Not calculated")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()