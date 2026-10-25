from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2] / "member3_analysis"

INPUT_FILE = (
    PROJECT_ROOT
    / "analysis"
    / "output"
    / "random_forest"
    / "risk_classifications.csv"
)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "random_forest_risk_map.png"

# Load Random Forest classifications
data = pd.read_csv(INPUT_FILE)

# Use the model's predicted categories
category_column = "rf_predicted_category"

risk_levels = ["Low", "Medium", "High"]
risk_codes = {"Low": 0, "Medium": 1, "High": 2}

data = data.dropna(
    subset=["latitude", "longitude", category_column]
).copy()

data["risk_code"] = data[category_column].map(risk_codes)
data = data.dropna(subset=["risk_code"])

# Plot the spatial grid
cmap = ListedColormap(["green", "gold", "red"])

fig, ax = plt.subplots(figsize=(12, 9))

scatter = ax.scatter(
    data["longitude"],
    data["latitude"],
    c=data["risk_code"],
    cmap=cmap,
    vmin=0,
    vmax=2,
    s=55,
    marker="s",
    edgecolors="black",
    linewidths=0.15,
)

legend_items = [
    Patch(facecolor="green", edgecolor="black", label="Low Risk"),
    Patch(facecolor="gold", edgecolor="black", label="Medium Risk"),
    Patch(facecolor="red", edgecolor="black", label="High Risk"),
]

ax.legend(handles=legend_items, title="Predicted Risk Category")
ax.set_title("Random Forest Preliminary Flood-Risk Screening Map")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.grid(True, linestyle="--", alpha=0.4)

fig.text(
    0.5,
    0.015,
    "Categories are heuristic screening labels, not validated flood probabilities.",
    ha="center",
    fontsize=9,
)

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
plt.close()

print(f"Risk map saved to: {OUTPUT_FILE}")
print("\nPredicted category counts:")
print(data[category_column].value_counts().reindex(risk_levels, fill_value=0))
