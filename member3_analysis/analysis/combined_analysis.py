import json
from pathlib import Path

from member3_analysis.analysis.river_analysis import analyse_rivers
from member3_analysis.analysis.rainfall_analysis import analyse_rainfall
from member3_analysis.mongodb.connection import get_database
from member3_analysis.mongodb.config import RAINFALL_COLLECTION


OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Exploratory index weights. These are not scientifically calibrated.
RAINFALL_WEIGHT = 0.5
LOW_ELEVATION_WEIGHT = 0.5


def analyse_march_rainfall():
    """Analyse March 1-4, 2025 rainfall separately from other periods."""
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


def calculate_preliminary_risk_index():
    """
    Calculate an exploratory rainfall-elevation index for March 2025.

    Scores range from 0 to 100. They are relative screening scores,
    not flood probabilities or validated flood predictions.
    """

    client, db = get_database()

    try:
        collection = db[RAINFALL_COLLECTION]

        # Average rainfall and elevation by grid cell across March 1-4.
        pipeline = [
            {
                "$match": {
                    "date": {
                        "$gte": "2025-03-01",
                        "$lte": "2025-03-04",
                    },
                    "elevation_mean": {"$ne": None},
                    "rainfall_mm": {"$ne": None},
                    "grid_row": {"$exists": True},
                    "grid_col": {"$exists": True},
                }
            },
            {
                "$group": {
                    "_id": {
                        "row": "$grid_row",
                        "col": "$grid_col",
                    },
                    "average_rainfall_mm": {
                        "$avg": "$rainfall_mm"
                    },
                    "elevation_mean": {
                        "$avg": "$elevation_mean"
                    },
                    "days_observed": {"$sum": 1},
                }
            },
            {
                "$match": {
                    "days_observed": {"$gt": 0}
                }
            },
        ]

        records = list(collection.aggregate(pipeline))

        if not records:
            return {
                "status": "No usable records",
                "period": "2025-03-01 to 2025-03-04",
                "grid_cells_scored": 0,
                "top_risk_cells": [],
                "interpretation": (
                    "No grid cells had usable rainfall and elevation "
                    "records for the selected period."
                ),
            }

        # Determine the normalization ranges from usable cells.
        max_rainfall = max(
            row["average_rainfall_mm"] for row in records
        )

        min_elevation = min(
            row["elevation_mean"] for row in records
        )

        max_elevation = max(
            row["elevation_mean"] for row in records
        )

        elevation_range = max_elevation - min_elevation

        scored_cells = []

        for row in records:
            rainfall = row["average_rainfall_mm"]
            elevation = row["elevation_mean"]

            # Normalize rainfall to 0-1.
            rainfall_score = (
                rainfall / max_rainfall
                if max_rainfall > 0
                else 0.0
            )

            # Lower elevation receives a higher score.
            low_elevation_score = (
                (max_elevation - elevation) / elevation_range
                if elevation_range > 0
                else 0.0
            )

            # Combine the two normalized indicators.
            risk_score = 100 * (
                RAINFALL_WEIGHT * rainfall_score
                + LOW_ELEVATION_WEIGHT * low_elevation_score
            )

            scored_cells.append({
                "grid_row": row["_id"]["row"],
                "grid_col": row["_id"]["col"],
                "average_rainfall_mm": round(rainfall, 2),
                "elevation_mean": round(elevation, 2),
                "rainfall_score": round(rainfall_score, 4),
                "low_elevation_score": round(
                    low_elevation_score, 4
                ),
                "preliminary_risk_index": round(risk_score, 2),
                "days_observed": row["days_observed"],
            })

        # Highest score first.
        scored_cells.sort(
            key=lambda cell: cell["preliminary_risk_index"],
            reverse=True,
        )

        return {
            "status": "Exploratory screening completed",
            "period": "2025-03-01 to 2025-03-04",
            "grid_cells_scored": len(scored_cells),
            "weights": {
                "rainfall": RAINFALL_WEIGHT,
                "low_elevation": LOW_ELEVATION_WEIGHT,
            },
            "formula": (
                "100 * (0.5 * rainfall_score "
                "+ 0.5 * low_elevation_score)"
            ),
            "normalization": {
                "rainfall": (
                    "Average cell rainfall divided by the maximum "
                    "average rainfall among scored cells."
                ),
                "low_elevation": (
                    "(Maximum cell elevation - cell elevation) / "
                    "(Maximum elevation - minimum elevation)."
                ),
            },
            "top_risk_cells": scored_cells[:10],
            "interpretation": (
                "Higher scores indicate higher relative values under "
                "this exploratory formula. They are not probabilities "
                "of flooding or validated flood-risk predictions."
            ),
            "limitations": [
                "The weights are illustrative and not calibrated.",
                (
                    "Elevation values of zero are retained but require "
                    "verification."
                ),
                "Records with missing elevation are excluded.",
                (
                    "Grid-cell geographic alignment has not been "
                    "validated."
                ),
                "No independent flood-event validation has been performed.",
                "River levels are not included in this index.",
                (
                    "The index uses rainfall and elevation only; it "
                    "does not represent all flood-driving factors."
                ),
            ],
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

    print("Calculating preliminary rainfall-elevation index...")
    risk_index_report = calculate_preliminary_risk_index()

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

        "preliminary_environmental_risk_index": risk_index_report,

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
                "March 1-4, 2025 rainfall was analysed separately. "
                "The daily maximum rainfall values were 42.60 mm, "
                "78.90 mm, 53.80 mm, and 7.30 mm, respectively. "
                "None reached the selected 100 mm screening threshold."
            ),
            "combined_risk_score": (
                "A preliminary rainfall-elevation screening index has "
                "been calculated for March 2025. River levels are not "
                "included because this index has not been spatially "
                "and temporally integrated with river observations."
            ),
        },

        "limitations": [
            (
                "Rainfall observations cover March 1-4, 2025 and "
                "August 1-4, 2025. River observations are available "
                "through March 10, 2025, but there are no river "
                "observations for March 1-4."
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
                "The preliminary index is exploratory and has not been "
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

    print("\n--- PRELIMINARY ENVIRONMENTAL RISK INDEX ---")
    print("Status:", risk_index_report["status"])
    print(
        "Grid cells scored:",
        risk_index_report["grid_cells_scored"],
    )

    for cell in risk_index_report["top_risk_cells"]:
        print(
            f"Grid ({cell['grid_row']}, {cell['grid_col']}): "
            f"score={cell['preliminary_risk_index']:.2f}, "
            f"rainfall={cell['average_rainfall_mm']:.2f} mm, "
            f"elevation={cell['elevation_mean']:.2f} m"
        )

    print(f"\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()