import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
ANALYSIS_FILE = BASE_DIR / "analysis" / "output" / "rainfall_analysis.json"
OUTPUT_DIR = BASE_DIR / "visualization" / "output"


def load_analysis():
    if not ANALYSIS_FILE.exists():
        raise FileNotFoundError(
            f"Rainfall analysis report not found: {ANALYSIS_FILE}\n"
            "Run: python -m member3_analysis.analysis.rainfall_analysis"
        )

    with ANALYSIS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = load_analysis()

    # ---------------------------------------------
    # Graph 1: Daily rainfall trends
    # ---------------------------------------------
    daily = pd.DataFrame(report["daily_summaries"])

    if not daily.empty:
        daily["date"] = pd.to_datetime(daily["date"])
        daily = daily.sort_values("date")

        plt.figure(figsize=(11, 6))

        plt.plot(
            daily["date"],
            daily["average_rainfall_mm"],
            marker="o",
            linewidth=2,
            label="Average rainfall",
        )

        plt.plot(
            daily["date"],
            daily["maximum_rainfall_mm"],
            marker="s",
            linewidth=2,
            label="Maximum rainfall",
        )

        plt.xlabel("Date")
        plt.ylabel("Rainfall (mm)")
        plt.title("Daily Rainfall Trends")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.3)
        plt.xticks(
            daily["date"],
            daily["date"].dt.strftime("%d %b %Y"),
            rotation=20,
        )
        plt.tight_layout()

        path = OUTPUT_DIR / "daily_rainfall_trends.png"
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: {path}")

    # ---------------------------------------------
    # Graph 2: Top 10 rainfall observations
    # ---------------------------------------------
    top = pd.DataFrame(report["top_10_rainfall_observations"])

    if not top.empty:
        top["label"] = top.apply(
            lambda row: (
                f"{row['date']} | "
                f"Grid ({row['grid_row']}, {row['grid_col']})"
            ),
            axis=1,
        )

        top = top.sort_values("rainfall_mm")

        plt.figure(figsize=(12, 7))
        bars = plt.barh(top["label"], top["rainfall_mm"])

        plt.bar_label(bars, fmt="%.1f mm", padding=4)
        plt.xlabel("Rainfall (mm)")
        plt.ylabel("Date and grid cell")
        plt.title("Top 10 Rainfall Observations")
        plt.grid(axis="x", linestyle="--", alpha=0.3)
        plt.tight_layout()

        path = OUTPUT_DIR / "top_10_rainfall_cells.png"
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: {path}")

    # ---------------------------------------------
    # Graph 3: Elevation data completeness
    # ---------------------------------------------
    quality = report["elevation_data_quality"]

    labels = [
        "No elevation",
        "Partial elevation",
        "Complete elevation",
    ]

    values = [
        quality["without_elevation"],
        quality["partial_elevation"],
        quality["complete_elevation"],
    ]

    plt.figure(figsize=(9, 6))
    bars = plt.bar(labels, values)

    plt.bar_label(bars, fmt="%d", padding=4)
    plt.ylabel("Number of Records")
    plt.title("Elevation Data Completeness")
    plt.grid(axis="y", linestyle="--", alpha=0.3)
    plt.tight_layout()

    path = OUTPUT_DIR / "elevation_data_quality.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")

    # ---------------------------------------------
    # Graph 4: Days flagged by rainfall screening
    # ---------------------------------------------
    if not daily.empty:
        daily["screening_label"] = daily[
            "heavy_rainfall_screen"
        ].map({
            True: "Threshold reached",
            False: "Below threshold",
        })

        plt.figure(figsize=(10, 6))

        bars = plt.bar(
            daily["date"].dt.strftime("%d %b"),
            daily["maximum_rainfall_mm"],
        )

        plt.axhline(
            report["heavy_rainfall_screening_threshold_mm"],
            linestyle="--",
            label="Screening threshold",
        )

        plt.bar_label(bars, fmt="%.1f", padding=3)
        plt.xlabel("Date")
        plt.ylabel("Maximum grid-cell rainfall (mm)")
        plt.title("Maximum Rainfall vs Screening Threshold")
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.3)
        plt.tight_layout()

        path = OUTPUT_DIR / "rainfall_screening_threshold.png"
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: {path}")

    print("Rainfall visualizations generated from rainfall_analysis.json.")


if __name__ == "__main__":
    main()