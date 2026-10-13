import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


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


def plot_river_indicators(ax, river):
    high_count = river["relative_high_level_station_count"]
    total_count = river["stations_analysed"]
    other_count = total_count - high_count

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


def plot_rainfall_trends(ax, rainfall):
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
        ax.plot(
            [item["date"][5:] for item in march_daily],
            [item["maximum_rainfall_mm"] for item in march_daily],
            marker="o",
            linewidth=2,
            label="March 2025",
        )

    if august_daily:
        ax.plot(
            [item["date"][5:] for item in august_daily],
            [item["maximum_rainfall_mm"] for item in august_daily],
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

    ax.set_title("Daily Maximum Rainfall")
    ax.set_ylabel("Maximum rainfall (mm)")
    ax.set_xlabel("Date (MM-DD)")
    ax.legend(fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.3)


def plot_elevation_quality(ax, elevation):
    labels = ["No elevation", "Partial", "Complete"]
    values = [
        elevation["without_elevation"],
        elevation["partial_elevation"],
        elevation["complete_elevation"],
    ]

    bars = ax.bar(labels, values)

    ax.set_title("Elevation Data Completeness")
    ax.set_ylabel("Number of records")
    ax.tick_params(axis="x", labelrotation=10)

    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(bar.get_height()):,}",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def plot_march_summary(ax, march, river, rainfall, risk_index):
    ax.axis("off")

    march_lines = [
        (
            f"{item['date']}: mean "
            f"{item['mean_rainfall_mm']:.2f} mm, "
            f"maximum {item['max_rainfall_mm']:.2f} mm"
        )
        for item in march["daily_summaries"]
    ]

    risk_status = (
        risk_index.get("status", "Unavailable")
        if risk_index
        else "Unavailable"
    )

    scored_cells = (
        risk_index.get("grid_cells_scored", 0)
        if risk_index
        else 0
    )

    summary = (
        "MARCH 2025 RAINFALL SCREENING\n\n"
        + "\n".join(march_lines)
        + "\n\n"
        f"Days reaching 100 mm threshold: "
        f"{march['days_reaching_100mm_screen']} "
        f"of {march['days_found']}\n\n"
        "OVERALL DATA SUMMARY\n\n"
        f"River stations: {river['stations_analysed']}\n"
        f"High relative-level stations: "
        f"{river['relative_high_level_station_count']}\n"
        f"Rainfall records: "
        f"{rainfall['records_analysed']:,}\n\n"
        "PRELIMINARY RISK INDEX\n\n"
        f"Status: {risk_status}\n"
        f"Grid cells scored: {scored_cells:,}\n\n"
        "LIMITATIONS\n\n"
        "• No river observations for March 1–4.\n"
        "• River levels are not official danger levels.\n"
        "• 100 mm is an internal screening threshold.\n"
        "• Grid coordinates are not verified locations.\n"
        "• Index is not a validated flood prediction."
    )

    ax.text(
        0.01,
        0.99,
        summary,
        transform=ax.transAxes,
        fontsize=8.5,
        va="top",
        linespacing=1.25,
        wrap=True,
    )

    ax.set_title("Screening Summary and Limitations", pad=10)


def plot_top_risk_cells(ax, risk_index):
    cells = sorted(
        risk_index.get("top_risk_cells", []),
        key=lambda cell: cell["preliminary_risk_index"],
        reverse=True,
    )[:10]

    if not cells:
        ax.text(
            0.5, 0.5, "No risk-index results available",
            ha="center", va="center",
        )
        ax.set_title("Top Grid Cells by Preliminary Risk Index")
        return

    labels = [
        f"({cell['grid_row']}, {cell['grid_col']})"
        for cell in cells
    ]

    scores = [
        cell["preliminary_risk_index"]
        for cell in cells
    ]

    bars = ax.barh(labels[::-1], scores[::-1])

    ax.set_title("Top 10 Grid Cells by Preliminary Risk Index")
    ax.set_xlabel("Risk index (0–100)")
    ax.set_xlim(0, 110)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.tick_params(axis="y", labelsize=8)

    for bar, score in zip(bars, scores[::-1]):
        ax.text(
            score + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.1f}",
            va="center",
            fontsize=8,
        )


def plot_risk_heatmap(ax, risk_index):
    cells = risk_index.get("top_risk_cells", [])

    if not cells:
        ax.text(
            0.5, 0.5, "No risk-index results available",
            ha="center", va="center",
        )
        ax.set_title("Preliminary Risk-Index Heatmap")
        return

    min_row = min(cell["grid_row"] for cell in cells)
    max_row = max(cell["grid_row"] for cell in cells)
    min_col = min(cell["grid_col"] for cell in cells)
    max_col = max(cell["grid_col"] for cell in cells)

    grid = np.full(
        (
            max_row - min_row + 1,
            max_col - min_col + 1,
        ),
        np.nan,
    )

    for cell in cells:
        row = cell["grid_row"] - min_row
        col = cell["grid_col"] - min_col

        grid[row, col] = cell["preliminary_risk_index"]

    image = ax.imshow(
        grid,
        origin="lower",
        aspect="auto",
        interpolation="nearest",
    )

    ax.set_title("Preliminary Environmental Risk-Index Heatmap")
    ax.set_xlabel("Grid column")
    ax.set_ylabel("Grid row")

    # Keep labels readable even when the grid is large.
    row_step = max(1, grid.shape[0] // 8)
    col_step = max(1, grid.shape[1] // 8)

    row_ticks = list(range(0, grid.shape[0], row_step))
    col_ticks = list(range(0, grid.shape[1], col_step))

    ax.set_yticks(row_ticks)
    ax.set_yticklabels([min_row + i for i in row_ticks])

    ax.set_xticks(col_ticks)
    ax.set_xticklabels([min_col + i for i in col_ticks])

    return image


def save_rainfall_risk_scatter(risk_index):
    cells = risk_index.get("top_risk_cells", [])

    if not cells:
        print("No scored cells; rainfall-risk scatter plot skipped.")
        return

    if not all("average_rainfall_mm" in cell for cell in cells):
        print(
            "average_rainfall_mm is unavailable; "
            "scatter plot skipped."
        )
        return

    rainfall_values = [
        cell["average_rainfall_mm"] for cell in cells
    ]

    scores = [
        cell["preliminary_risk_index"] for cell in cells
    ]

    fig, ax = plt.subplots(figsize=(9, 6))

    scatter = ax.scatter(
        rainfall_values,
        scores,
        c=scores,
        s=55,
    )

    fig.colorbar(
        scatter,
        ax=ax,
        label="Preliminary risk index",
    )

    ax.set_title("Average Rainfall versus Preliminary Risk Index")
    ax.set_xlabel("Average rainfall (mm)")
    ax.set_ylabel("Preliminary risk index (0–100)")
    ax.grid(True, linestyle="--", alpha=0.3)

    fig.text(
        0.5,
        0.01,
        "Exploratory relationship, not a validated flood prediction.",
        ha="center",
        fontsize=9,
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    output_path = OUTPUT_DIR / "rainfall_vs_preliminary_risk.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Rainfall-risk scatter plot saved to: {output_path}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = load_report()

    river = report["river_analysis"]
    rainfall = report["rainfall_analysis"]
    march = report["march_2025_rainfall_screening"]
    elevation = report["elevation_data_quality"]
    risk_index = report.get("preliminary_environmental_risk_index", {})

    # Six-panel combined dashboard
    fig, axes = plt.subplots(3, 2, figsize=(17, 18))

    fig.suptitle(
        "Kerala Flood-Risk Assessment Dashboard",
        fontsize=19,
        fontweight="bold",
        y=0.99,
    )

    plot_river_indicators(axes[0, 0], river)
    plot_rainfall_trends(axes[0, 1], rainfall)
    plot_elevation_quality(axes[1, 0], elevation)
    plot_march_summary(
        axes[1, 1], march, river, rainfall, risk_index
    )
    plot_top_risk_cells(axes[2, 0], risk_index)

    image = plot_risk_heatmap(axes[2, 1], risk_index)

    if image is not None:
        fig.colorbar(
            image,
            ax=axes[2, 1],
            fraction=0.046,
            pad=0.04,
            label="Preliminary risk index (0–100)",
        )

    fig.text(
        0.5,
        0.015,
        (
            "Exploratory screening only — not a validated flood prediction. "
            "Grid-index heatmap is not a geographic map."
        ),
        ha="center",
        fontsize=10,
    )

    plt.tight_layout(rect=[0, 0.035, 1, 0.97])

    output_path = OUTPUT_DIR / "combined_risk_dashboard.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Combined six-panel dashboard saved to: {output_path}")

    # Keep the rainfall-risk scatter plot as a separate visualization.
    if risk_index.get("status") in (
        "success",
        "Exploratory screening completed",
    ):
        save_rainfall_risk_scatter(risk_index)
    else:
        print("Risk index unavailable; scatter plot skipped.")


if __name__ == "__main__":
    main()