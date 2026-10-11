import json
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parents[1]
ANALYSIS_FILE = (
    BASE_DIR / "analysis" / "output" / "combined_risk_assessment.json"
)
OUTPUT_DIR = BASE_DIR / "visualization" / "output"


def load_report():
    if not ANALYSIS_FILE.exists():
        raise FileNotFoundError(
            f"Cannot find {ANALYSIS_FILE}\n"
            "Run the analysis scripts first."
        )

    with ANALYSIS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = load_report()

    river = report["river_analysis"]
    rainfall = report["rainfall_analysis"]
    elevation = report["elevation_data_quality"]

    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle(
        "Kerala Flood-Risk Assessment Dashboard",
        fontsize=17,
        fontweight="bold",
    )

    # 1. Historical river indicators
    ax = axes[0, 0]
    high_count = river["relative_high_level_station_count"]
    other_count = river["stations_analysed"] - high_count

    ax.bar(
        ["High relative\nhistorical level", "Other stations"],
        [high_count, other_count],
    )
    ax.set_title("Historical River-Level Indicators")
    ax.set_ylabel("Number of stations")

    for i, value in enumerate([high_count, other_count]):
        ax.text(i, value, str(value), ha="center", va="bottom")

    # 2. Daily maximum rainfall
    ax = axes[0, 1]
    daily = rainfall["daily_summaries"]

    dates = [item["date"] for item in daily]
    maxima = [item["maximum_rainfall_mm"] for item in daily]

    ax.plot(dates, maxima, marker="o", linewidth=2)
    ax.set_title("Daily Maximum Rainfall")
    ax.set_ylabel("Rainfall (mm)")
    ax.set_xlabel("Date")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(True, linestyle="--", alpha=0.3)

    # 3. Elevation data quality
    ax = axes[1, 0]
    labels = ["No elevation", "Partial", "Complete"]
    values = [
        elevation["without_elevation"],
        elevation["partial_elevation"],
        elevation["complete_elevation"],
    ]

    bars = ax.bar(labels, values)
    ax.set_title("Elevation Data Completeness")
    ax.set_ylabel("Number of records")

    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(bar.get_height()):,}",
            ha="center",
            va="bottom",
        )

    # 4. Interpretation and limitations
    ax = axes[1, 1]
    ax.axis("off")

    summary = (
        "ASSESSMENT SUMMARY\n\n"
        f"River stations analysed: {river['stations_analysed']}\n"
        f"Rainfall days analysed: {rainfall['days_analysed']}\n"
        f"Rainfall records: {rainfall['records_analysed']:,}\n\n"
        "IMPORTANT LIMITATIONS\n\n"
        "• River and rainfall periods do not overlap.\n"
        "• Relative river levels are not official danger levels.\n"
        "• Rainfall screening is not a flood warning.\n"
        "• No validated combined risk score is calculated.\n"
    )

    ax.text(
        0.03,
        0.97,
        summary,
        transform=ax.transAxes,
        fontsize=11,
        va="top",
        linespacing=1.5,
    )

    fig.text(
        0.5,
        0.015,
        "Preliminary descriptive assessment — not a validated flood prediction",
        ha="center",
        fontsize=10,
    )

    plt.tight_layout(rect=[0, 0.04, 1, 0.94])

    output_path = OUTPUT_DIR / "combined_risk_dashboard.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Combined assessment dashboard saved to: {output_path}")


if __name__ == "__main__":
    main()