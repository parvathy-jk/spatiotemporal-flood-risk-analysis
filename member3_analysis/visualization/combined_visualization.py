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
    march = report["march_2025_rainfall_screening"]
    elevation = report["elevation_data_quality"]

    # Create dashboard
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

    bars = ax.bar(
        ["High relative\nhistorical level", "Other stations"],
        [high_count, other_count],
    )

    ax.set_title("Historical River-Level Indicators")
    ax.set_ylabel("Number of stations")

    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(bar.get_height())}",
            ha="center",
            va="bottom",
        )

    # 2. Daily maximum rainfall, separated by month
    ax = axes[0, 1]

    daily = sorted(
        rainfall["daily_summaries"],
        key=lambda item: item["date"],
    )

    march_daily = [
        item for item in daily
        if item["date"].startswith("2025-03")
    ]
    august_daily = [
        item for item in daily
        if item["date"].startswith("2025-08")
    ]

    if march_daily:
        march_dates = [item["date"][5:] for item in march_daily]
        march_maxima = [
            item["maximum_rainfall_mm"] for item in march_daily
        ]

        ax.plot(
            march_dates,
            march_maxima,
            marker="o",
            linewidth=2,
            label="March 2025",
        )

    if august_daily:
        august_dates = [item["date"][5:] for item in august_daily]
        august_maxima = [
            item["maximum_rainfall_mm"] for item in august_daily
        ]

        ax.plot(
            august_dates,
            august_maxima,
            marker="s",
            linewidth=2,
            label="August 2025",
        )

    ax.axhline(
        y=100,
        linestyle="--",
        linewidth=1.5,
        label="100 mm screening threshold",
    )

    ax.set_title("Daily Maximum Rainfall by Period")
    ax.set_ylabel("Maximum rainfall (mm)")
    ax.set_xlabel("Date (MM-DD)")
    ax.legend()
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

    # 4. March screening results and limitations
    ax = axes[1, 1]
    ax.axis("off")

    march_lines = [
        (
            f"{item['date']}: mean "
            f"{item['mean_rainfall_mm']:.2f} mm, "
            f"maximum {item['max_rainfall_mm']:.2f} mm"
        )
        for item in march["daily_summaries"]
    ]

    summary = (
        "MARCH 2025 RAINFALL SCREENING\n\n"
        + "\n".join(march_lines)
        + "\n\n"
        f"Days reaching 100 mm threshold: "
        f"{march['days_reaching_100mm_screen']}"
        f" of {march['days_found']}\n\n"
        "OVERALL DATA SUMMARY\n\n"
        f"River stations: {river['stations_analysed']}\n"
        f"High relative-level stations: {high_count}\n"
        f"Rainfall records: {rainfall['records_analysed']:,}\n"
        f"Rainfall days across both periods: "
        f"{rainfall['days_analysed']}\n\n"
        "LIMITATIONS\n\n"
        "• No river observations for March 1–4.\n"
        "• River levels are not official danger levels.\n"
        "• The 100 mm threshold is not an official warning.\n"
        "• Geographic coordinates require verification.\n"
        "• No validated combined risk score is calculated."
    )

    ax.text(
        0.02,
        0.98,
        summary,
        transform=ax.transAxes,
        fontsize=9.5,
        va="top",
        linespacing=1.35,
        wrap=True,
    )

    fig.text(
        0.5,
        0.015,
        (
            "Preliminary descriptive assessment — "
            "not a validated flood prediction"
        ),
        ha="center",
        fontsize=10,
    )

    plt.tight_layout(rect=[0, 0.04, 1, 0.94])

    output_path = OUTPUT_DIR / "combined_risk_dashboard.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Combined assessment dashboard saved to: {output_path}")
    print(f"March rainfall days displayed: {len(march_daily)}")
    print(f"August rainfall days displayed: {len(august_daily)}")


if __name__ == "__main__":
    main()