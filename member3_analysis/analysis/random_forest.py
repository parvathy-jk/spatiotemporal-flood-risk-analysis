"""
Random Forest Classification for Preliminary Flood-Risk Screening.

This model learns low, medium and high screening categories derived
from the project's existing rainfall-elevation risk index.

It does NOT predict verified flood events or flood probabilities.
"""

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# PATHS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    ROOT
    / "results"
    / "spark"
    / "rainfall_elevation_sep_oct_2024"
)

OUTPUT_DIR = ROOT / "member3_analysis" / "analysis" / "output"
MODEL_DIR = OUTPUT_DIR / "random_forest"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

RANDOM_STATE = 42

FEATURES = [
    "rainfall_mean_mm",
    "elevation_mean",
    "elevation_min",
    "elevation_max",
    "elevation_coverage",
]

CLASS_NAMES = ["Low", "Medium", "High"]


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def load_data():
    files = sorted(DATA_FILE.glob("part-*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No Spark CSV part files found in {DATA_FILE}"
        )

    frames = [pd.read_csv(file) for file in files]
    data = pd.concat(frames, ignore_index=True)

    required = {
        "grid_row",
        "grid_col",
        "date",
        "rainfall_mm",
        "elevation_valid_pixels",
        "elevation_missing_pixels",
        "elevation_mean",
        "elevation_min",
        "elevation_max",
    }

    missing = required - set(data.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date", "rainfall_mm"]).copy()

    data["elevation_coverage"] = (
        data["elevation_valid_pixels"]
        / (
            data["elevation_valid_pixels"]
            + data["elevation_missing_pixels"]
        ).replace(0, np.nan)
    )

    # Treat elevation values of zero as observed values.
    # Only actual missing values are imputed.

    # Average each cell's observations over the 14-day period.
    cell_data = (
        data.groupby(["grid_row", "grid_col"], as_index=False)
        .agg(
            rainfall_mean_mm=("rainfall_mm", "mean"),
            elevation_mean=("elevation_mean", "mean"),
            elevation_min=("elevation_min", "mean"),
            elevation_max=("elevation_max", "mean"),
            elevation_coverage=("elevation_coverage", "mean"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            days_observed=("date", "nunique"),
        )
    )

    return cell_data


# --------------------------------------------------
# CREATE SCREENING LABELS
# --------------------------------------------------

def create_labels(data):
    """
    Create screening categories from a transparent heuristic.

    This is a newly defined index using available data.
    It is not claimed to reproduce the exact scores in
    combined_risk_assessment.json.
    """

    data = data.copy()

    valid_elevation = data["elevation_mean"].notna()

    if valid_elevation.sum() < 3:
        raise ValueError(
            "Not enough cells with valid elevation to classify."
        )

    # Normalize rainfall among valid cells.
    rain_min = data.loc[valid_elevation, "rainfall_mean_mm"].min()
    rain_max = data.loc[valid_elevation, "rainfall_mean_mm"].max()

    if rain_max == rain_min:
        rainfall_score = pd.Series(0.0, index=data.index)
    else:
        rainfall_score = (
            (data["rainfall_mean_mm"] - rain_min)
            / (rain_max - rain_min)
        )

    # Lower elevation receives a higher score.
    elev_min = data.loc[valid_elevation, "elevation_mean"].min()
    elev_max = data.loc[valid_elevation, "elevation_mean"].max()

    if elev_max == elev_min:
        elevation_score = pd.Series(0.0, index=data.index)
    else:
        elevation_score = (
            (elev_max - data["elevation_mean"])
            / (elev_max - elev_min)
        )

    data["screening_score"] = (
        100 * 0.5 * rainfall_score
        + 100 * 0.5 * elevation_score
    )

    # Classify scores into three screening categories.
    # These are heuristic thresholds, not flood thresholds.
    data["risk_category"] = pd.cut(
        data["screening_score"],
        bins=[-np.inf, 33.3333, 66.6667, np.inf],
        labels=CLASS_NAMES,
        include_lowest=True,
    )

    data.loc[~valid_elevation, "risk_category"] = np.nan

    return data


# --------------------------------------------------
# TRAIN AND EVALUATE
# --------------------------------------------------

def train_model(data):
    usable = data.dropna(subset=["risk_category"]).copy()

    X = usable[FEATURES].replace([np.inf, -np.inf], np.nan)
    y = usable["risk_category"].astype(str)

    class_counts = y.value_counts()

    if len(class_counts) < 2 or class_counts.min() < 2:
        raise ValueError(
            "At least two screening classes are needed, "
            "with at least two samples per class."
        )

    # Spatial holdout: reserve entire grid rows for testing.
    test_rows = {26, 27, 28, 29}

    test_mask = usable["grid_row"].isin(test_rows)

    X_train = X.loc[~test_mask]
    X_test = X.loc[test_mask]
    y_train = y.loc[~test_mask]
    y_test = y.loc[test_mask]

    if X_test.empty or X_train.empty:
        raise ValueError("Spatial split produced an empty train or test set.")

    if y_train.nunique() < 2:
        raise ValueError("Training set must contain at least two classes.")

    print("Spatial holdout rows:", sorted(test_rows))
    print("Training class counts:")
    print(y_train.value_counts().to_string())
    print("Testing class counts:")
    print(y_test.value_counts().to_string())

    model = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=12,
                    min_samples_leaf=3,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0,
    )

    report = classification_report(
        y_test,
        predictions,
        labels=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=CLASS_NAMES,
    )

    # Save the trained pipeline.
    joblib.dump(model, MODEL_DIR / "random_forest_model.joblib")

    # Save metrics.
    metrics = {
        "model": "Random Forest classifier",
        "purpose": "Reproduce heuristic screening categories",
        "target": "risk_category",
        "features": FEATURES,
        "rows_used": int(len(usable)),
        "training_rows": int(len(X_train)),
        "testing_rows": int(len(X_test)),
        "class_distribution": {
            str(k): int(v)
            for k, v in class_counts.items()
        },
        "accuracy": float(accuracy),
        "macro_f1": float(macro_f1),
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "class_order": CLASS_NAMES,
        "limitations": [
            "Labels are heuristic categories, not verified flood labels.",
            "Evaluation measures reproduction of those categories.",
            "Random cell-level splitting may overestimate generalization.",
            "The screening score is not a flood probability.",
            "Spatial alignment and elevation quality require validation.",
        ],
    }

    with open(MODEL_DIR / "model_metrics.json", "w") as file:
        json.dump(metrics, file, indent=2)

    # Save the confusion matrix plot.
    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=CLASS_NAMES,
    )
    display.plot(values_format="d")
    plt.title("Random Forest: Screening Category Classification")
    plt.tight_layout()
    plt.savefig(
        MODEL_DIR / "confusion_matrix.png",
        dpi=200,
    )
    plt.close()

    # Save feature importance.
    classifier = model.named_steps["classifier"]

    importance = pd.DataFrame(
        {
            "feature": FEATURES,
            "importance": classifier.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    importance.to_csv(
        MODEL_DIR / "feature_importance.csv",
        index=False,
    )

    importance_plot = importance.sort_values("importance")

    plt.figure(figsize=(9, 5))
    plt.barh(
        importance_plot["feature"],
        importance_plot["importance"],
    )
    plt.xlabel("Feature Importance")
    plt.title("Random Forest Feature Importance")
    plt.tight_layout()
    plt.savefig(
        MODEL_DIR / "feature_importance.png",
        dpi=200,
    )
    plt.close()

    # Predict categories for all usable cells.
    # These are model classifications, not flood probabilities.
    all_predictions = model.predict(X)

    usable["rf_predicted_category"] = all_predictions

    probabilities = model.predict_proba(X)

    for index, category in enumerate(model.classes_):
        usable[f"model_probability_{category.lower()}"] = (
            probabilities[:, index]
        )

    usable.to_csv(
        MODEL_DIR / "risk_classifications.csv",
        index=False,
    )

    print("\nRANDOM FOREST SCREENING CLASSIFIER")
    print("-" * 45)
    print(f"Usable grid cells: {len(usable)}")
    print(f"Training rows: {len(X_train)}")
    print(f"Testing rows: {len(X_test)}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1-score: {macro_f1:.4f}")

    print("\nClass distribution:")
    print(class_counts.to_string())

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            labels=CLASS_NAMES,
            zero_division=0,
        )
    )

    print("\nFeature importance:")
    print(importance.to_string(index=False))

    print(f"\nOutputs saved in: {MODEL_DIR}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    print("Loading rainfall and elevation data...")
    data = load_data()

    print(f"Grid cells loaded: {len(data)}")

    print("Creating heuristic screening categories...")
    data = create_labels(data)

    print("Training and evaluating Random Forest...")
    train_model(data)


if __name__ == "__main__":
    main()
