from pathlib import Path
import json

import pandas as pd


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "river"
    / "rwl_tel_hr_kerala_sw_999_2021_2025.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "river_clean.csv"
REPORT_FILE = OUTPUT_DIR / "river_quality_report.json"


def clean_river_data():
    """Inspect, validate and prepare the river water-level dataset."""

    print("=" * 60)
    print("KERALA RIVER WATER-LEVEL DATA PREPROCESSING")
    print("=" * 60)

    # Check input file
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"River dataset not found: {INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Read CSV
    print("\nReading original dataset...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    original_rows = len(df)

    print("Original rows:", original_rows)
    print("Original columns:", len(df.columns))

    # Check required columns
    timestamp_col = "Data Acquisition Time"
    level_col = "River Water Level Telemetry Hourly (meter)"

    required_columns = [timestamp_col, level_col]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"Required column not found: {column}"
            )

    # Report duplicate records before removing anything
    exact_duplicates = int(df.duplicated().sum())

    print("\nExact duplicate rows:", exact_duplicates)

    # Parse timestamps using the format shown in the source data.
    # Any values that do not match are counted for the report.
    df[timestamp_col] = pd.to_datetime(
        df[timestamp_col],
        format="%d-%m-%Y %H:%M",
        errors="coerce"
    )

    invalid_timestamps = int(df[timestamp_col].isna().sum())

    print("Invalid or missing timestamps:", invalid_timestamps)

    # Convert the measured water level to numeric values
    df[level_col] = pd.to_numeric(
        df[level_col],
        errors="coerce"
    )

    invalid_levels = int(df[level_col].isna().sum())

    print("Missing or non-numeric water levels:", invalid_levels)

    # Convert coordinates when those columns are available
    coordinate_columns = ["Latitude", "Longitude"]

    for column in coordinate_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    invalid_coordinates = 0

    if all(column in df.columns for column in coordinate_columns):
        invalid_coordinate_mask = (
            df["Latitude"].isna()
            | df["Longitude"].isna()
            | ~df["Latitude"].between(-90, 90)
            | ~df["Longitude"].between(-180, 180)
        )

        invalid_coordinates = int(
            invalid_coordinate_mask.sum()
        )

        print("Rows with invalid coordinates:", invalid_coordinates)

    # Remove exact duplicate records
    df = df.drop_duplicates().copy()

    # Remove records without usable timestamps or water levels.
    # These records cannot be used reliably for time-series analysis.
    df = df.dropna(
        subset=[timestamp_col, level_col]
    ).copy()

    # Sort chronologically, retaining all other source columns
    df = df.sort_values(
        by=timestamp_col
    ).reset_index(drop=True)

    # Save cleaned CSV
    df.to_csv(
        OUTPUT_FILE,
        index=False,
        date_format="%Y-%m-%d %H:%M:%S"
    )

    # Prepare data-quality report
    report = {
        "dataset": INPUT_FILE.name,
        "original_rows": original_rows,
        "original_columns": len(df.columns),
        "exact_duplicate_rows_detected": exact_duplicates,
        "invalid_timestamps_detected": invalid_timestamps,
        "invalid_water_levels_detected": invalid_levels,
        "invalid_coordinate_rows_detected": invalid_coordinates,
        "cleaned_rows": len(df),
        "rows_removed": original_rows - len(df),
        "remaining_missing_values": {
            str(column): int(count)
            for column, count in df.isna().sum().items()
            if count > 0
        },
        "water_level_unit_from_source_column": "meter",
        "timestamp_column": timestamp_col,
        "water_level_column": level_col,
        "cleaned_file": str(OUTPUT_FILE.name)
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as report_file:
        json.dump(
            report,
            report_file,
            indent=4,
            ensure_ascii=False
        )

    print("\nPreprocessing completed.")
    print("Cleaned rows:", len(df))
    print("Rows removed:", original_rows - len(df))
    print("Cleaned dataset:", OUTPUT_FILE)
    print("Quality report:", REPORT_FILE)

    print("\nWater-level summary:")
    print(df[level_col].describe())

    print("\nFirst five cleaned records:")
    print(df.head())


if __name__ == "__main__":
    clean_river_data()
