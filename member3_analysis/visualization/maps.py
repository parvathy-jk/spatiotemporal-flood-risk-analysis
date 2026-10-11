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
    observations = pd.DataFrame(
        report["top_10_rainfall_observations"]
    )

    if observations.empty:
        print("No rainfall observations available for mapping.")
        return

    # Plot grid positions, not geographic coordinates.
    plt.figure(figsize=(11, 8))

    points = plt.scatter(
        observations["grid_col"],
        observations["grid_row"],
        c=observations["rainfall_mm"],
        s=160,
        marker="s",
    )

    plt.colorbar(points, label="Rainfall (mm)")
    plt.xlabel("Grid Column")
    plt.ylabel("Grid Row")
    plt.title("Locations of the Top 10 Rainfall Observations")
    plt.gca().invert_yaxis()
    plt.grid(True, linestyle="--", alpha=0.25)

    # Annotate each grid cell with its rainfall value.
    for _, row in observations.iterrows():
        plt.annotate(
            f"{row['rainfall_mm']:.1f} mm",
            (
                row["grid_col"],
                row["grid_row"],
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    plt.tight_layout()

    path = OUTPUT_DIR / "rainfall_grid_heatmap.png"
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Saved: {path}")
    print(
        "This visualization uses grid indices and the top 10 "
        "observations from rainfall_analysis.json."
    )
    print(
        "It is not a geographically verified map of Kerala."
    )


if __name__ == "__main__":
    main()