import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
ANALYSIS_FILE = BASE_DIR / "analysis" / "output" / "river_analysis.json"
OUTPUT_DIR = BASE_DIR / "visualization" / "output"


def load_analysis():
    if not ANALYSIS_FILE.exists():
        raise FileNotFoundError(
            f"River analysis report not found: {ANALYSIS_FILE}\n"
            "Run: python -m member3_analysis.analysis.river_analysis"
        )

    with ANALYSIS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = load_analysis()

    # ---------------------------------------------
    # Graph 1: Average water level by district
    # ---------------------------------------------
    districts = pd.DataFrame(report["district_summaries"])

    if not districts.empty:
        districts = districts.sort_values("average_water_level")

        plt.figure(figsize=(12, 7))
        bars = plt.barh(
            districts["district"],
            districts["average_water_level"],
        )

        plt.bar_label(bars, fmt="%.2f", padding=4)
        plt.xlabel("Average Water Level (source units)")
        plt.ylabel("District")
        plt.title("District-wise Average River Water Level")
        plt.grid(axis="x", linestyle="--", alpha=0.3)
        plt.tight_layout()

        path = OUTPUT_DIR / "district_average_water_level.png"
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: {path}")

        # ---------------------------------------------
        # Graph 2: Maximum water level by district
        # ---------------------------------------------
        districts = districts.sort_values("maximum_water_level")

        plt.figure(figsize=(12, 7))
        bars = plt.barh(
            districts["district"],
            districts["maximum_water_level"],
        )

        plt.bar_label(bars, fmt="%.2f", padding=4)
        plt.xlabel("Maximum Recorded Water Level (source units)")
        plt.ylabel("District")
        plt.title("District-wise Maximum Recorded River Water Level")
        plt.grid(axis="x", linestyle="--", alpha=0.3)
        plt.tight_layout()

        path = OUTPUT_DIR / "district_maximum_water_level.png"
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Saved: {path}")

    # ---------------------------------------------
    # Graph 3: Stations with high relative levels
    # ---------------------------------------------
    stations = pd.DataFrame(report["station_summaries"])

    if not stations.empty:
        high_stations = stations[
            stations["relative_level_flag"] == "HIGH_RELATIVE_TO_DATA"
        ].copy()

        if high_stations.empty:
            print("No stations met the relative high-level criterion.")
        else:
            high_stations = high_stations.sort_values(
                "maximum_water_level"
            )

            high_stations["label"] = (
                high_stations["station"]
                + " ("
                + high_stations["district"]
                + ")"
            )

            plt.figure(figsize=(12, 7))
            bars = plt.barh(
                high_stations["label"],
                high_stations["maximum_water_level"],
            )

            plt.bar_label(bars, fmt="%.2f", padding=4)
            plt.xlabel("Maximum Recorded Water Level (source units)")
            plt.ylabel("Station")
            plt.title(
                "Stations with High Relative Historical Water Levels"
            )
            plt.grid(axis="x", linestyle="--", alpha=0.3)
            plt.tight_layout()

            path = OUTPUT_DIR / "high_relative_river_stations.png"
            plt.savefig(path, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Saved: {path}")

    print("River visualizations generated from river_analysis.json.")


if __name__ == "__main__":
    main()