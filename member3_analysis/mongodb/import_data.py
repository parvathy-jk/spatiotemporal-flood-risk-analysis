from pathlib import Path

import pandas as pd
from pymongo import ASCENDING, UpdateOne
from pymongo.errors import BulkWriteError

from member3_analysis.mongodb.connection import get_database
from member3_analysis.mongodb.config import (
    RIVER_COLLECTION,
    RAINFALL_COLLECTION,
    RIVER_FILE,
    RAINFALL_FILE,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


RIVER_COLUMNS = [
    "station",
    "district",
    "date",
    "count",
    "average_water_level",
    "minimum_water_level",
    "maximum_water_level",
    "latitude",
    "longitude",
]


def clean_records(df):
    """Convert Pandas records into MongoDB-compatible dictionaries."""
    df = df.astype(object).where(pd.notna(df), None)
    return df.to_dict(orient="records")


def import_river_data(db):
    path = PROJECT_ROOT / RIVER_FILE

    if not path.exists():
        raise FileNotFoundError(f"River file not found: {path}")

    df = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=RIVER_COLUMNS,
    )

    df["date"] = pd.to_datetime(
        df["date"], errors="raise"
    ).dt.strftime("%Y-%m-%d")

    for column in [
        "count",
        "average_water_level",
        "minimum_water_level",
        "maximum_water_level",
        "latitude",
        "longitude",
    ]:
        df[column] = pd.to_numeric(df[column], errors="raise")

    records = clean_records(df)

    collection = db[ RIVER_COLLECTION ]

    collection.create_index(
        [
            ("station", ASCENDING),
            ("district", ASCENDING),
            ("date", ASCENDING),
        ],
        unique=True,
        name="unique_station_district_date",
    )

    operations = [
        UpdateOne(
            {
                "station": record["station"],
                "district": record["district"],
                "date": record["date"],
            },
            {"$set": record},
            upsert=True,
        )
        for record in records
    ]

    if operations:
        result = collection.bulk_write(operations, ordered=False)
        print(
            f"River data: {len(records)} records processed; "
            f"{result.upserted_count} inserted, "
            f"{result.modified_count} updated."
        )


def import_rainfall_data(db):
    path = PROJECT_ROOT / RAINFALL_FILE

    if not path.exists():
        raise FileNotFoundError(f"Rainfall file not found: {path}")

    df = pd.read_csv(path)

    expected_columns = [
        "grid_row",
        "grid_col",
        "date",
        "latitude",
        "longitude",
        "rainfall_mm",
        "elevation_valid_pixels",
        "elevation_missing_pixels",
        "elevation_mean",
        "elevation_min",
        "elevation_max",
    ]

    missing_columns = set(expected_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Rainfall CSV is missing columns: {sorted(missing_columns)}"
        )

    df["date"] = pd.to_datetime(
        df["date"], errors="raise"
    ).dt.strftime("%Y-%m-%d")

    records = clean_records(df)

    collection = db[RAINFALL_COLLECTION]

    collection.create_index(
        [
            ("grid_row", ASCENDING),
            ("grid_col", ASCENDING),
            ("date", ASCENDING),
        ],
        unique=True,
        name="unique_grid_cell_date",
    )

    operations = [
        UpdateOne(
            {
                "grid_row": record["grid_row"],
                "grid_col": record["grid_col"],
                "date": record["date"],
            },
            {"$set": record},
            upsert=True,
        )
        for record in records
    ]

    if operations:
        result = collection.bulk_write(operations, ordered=False)
        print(
            f"Rainfall/elevation data: {len(records)} records processed; "
            f"{result.upserted_count} inserted, "
            f"{result.modified_count} updated."
        )


def main():
    client, db = get_database()

    try:
        import_river_data(db)
        import_rainfall_data(db)

        print("\n--- IMPORT SUMMARY ---")
        print(
            f"River collection: "
            f"{db[RIVER_COLLECTION].count_documents({})} records"
        )
        print(
            f"Rainfall/elevation collection: "
            f"{db[RAINFALL_COLLECTION].count_documents({})} records"
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()