#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import math

import numpy as np
import rasterio
from rasterio.windows import Window

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    LongType,
)


PROJECT_ROOT = Path.cwd()

RAINFALL_DIR = (
    PROJECT_ROOT / "member1_data/data/processed/rainfall_kerala"
)

ELEVATION_PATH = (
    PROJECT_ROOT
    / "member1_data/data/processed/elevation/elevation_kerala_bbox.tif"
)

OUTPUT_DIR = PROJECT_ROOT / "results/spark/rainfall_elevation"

# The rainfall grid is 40 x 50.
# Verify the elevation-to-rainfall alignment before using this ratio.
ELEVATION_PIXELS_PER_RAINFALL_CELL = 120


def extract_date(filename):
    """Extract YYYYMMDD from the IMERG filename."""
    marker = ".2025"
    start = filename.find(marker)

    if start == -1:
        raise ValueError(f"Cannot identify date in {filename}")

    return datetime.strptime(
        filename[start + 1:start + 9], "%Y%m%d"
    ).strftime("%Y-%m-%d")


def build_elevation_records(rain_src, elevation_src):
    """Aggregate elevation pixels into matching rainfall grid cells."""

    if rain_src.crs != elevation_src.crs:
        raise ValueError("Rainfall and elevation CRS do not match.")

    if not np.allclose(
        [
            rain_src.bounds.left,
            rain_src.bounds.bottom,
            rain_src.bounds.right,
            rain_src.bounds.top,
        ],
        [
            elevation_src.bounds.left,
            elevation_src.bounds.bottom,
            elevation_src.bounds.right,
            elevation_src.bounds.top,
        ],
        atol=1e-5,
    ):
        raise ValueError("Rainfall and elevation bounds do not match.")

    ratio = ELEVATION_PIXELS_PER_RAINFALL_CELL

    expected_width = rain_src.width * ratio
    expected_height = rain_src.height * ratio

    if (
        elevation_src.width != expected_width
        or elevation_src.height != expected_height
    ):
        raise ValueError(
            "Unexpected raster dimensions. "
            "Check the grid alignment before aggregating."
        )

    records = []

    for row in range(rain_src.height):
        for col in range(rain_src.width):

            window = Window(
                col_off=col * ratio,
                row_off=row * ratio,
                width=ratio,
                height=ratio,
            )

            block = elevation_src.read(
                1, window=window, masked=True
            )

            values = block.compressed()
            values = values[np.isfinite(values)]

            latitude, longitude = rain_src.xy(row, col)

            if values.size:
                elevation_mean = float(values.mean())
                elevation_min = float(values.min())
                elevation_max = float(values.max())
            else:
                elevation_mean = None
                elevation_min = None
                elevation_max = None

            records.append({
                "grid_row": row,
                "grid_col": col,
                "latitude": float(latitude),
                "longitude": float(longitude),
                "elevation_valid_pixels": int(values.size),
                "elevation_missing_pixels": int(
                    block.size - values.size
                ),
                "elevation_mean": elevation_mean,
                "elevation_min": elevation_min,
                "elevation_max": elevation_max,
            })

    return records


def main():
    rainfall_files = sorted(RAINFALL_DIR.glob("*.tif"))

    if len(rainfall_files) != 4:
        raise ValueError(
            f"Expected four rainfall GeoTIFFs, found {len(rainfall_files)}"
        )

    if not ELEVATION_PATH.exists():
        raise FileNotFoundError(ELEVATION_PATH)

    with rasterio.open(rainfall_files[0]) as rain_src, \
         rasterio.open(ELEVATION_PATH) as elevation_src:

        elevation_records = build_elevation_records(
            rain_src, elevation_src
        )

    rainfall_records = []

    for path in rainfall_files:
        date = extract_date(path.name)

        with rasterio.open(path) as src:
            for row in range(src.height):
                values = src.read(
                    1, window=Window(0, row, src.width, 1),
                    masked=True
                )

                for col in range(src.width):
                    value = values[0, col]

                    if np.ma.is_masked(value):
                        continue

                    value = float(value)

                    if not math.isfinite(value):
                        continue

                    latitude, longitude = src.xy(row, col)

                    rainfall_records.append({
                        "date": date,
                        "grid_row": row,
                        "grid_col": col,
                        "latitude": float(latitude),
                        "longitude": float(longitude),
                        "rainfall_mm": value,
                    })

    spark = (
        SparkSession.builder
        .appName("KeralaRainfallElevationAnalysis")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    rainfall_schema = StructType([
        StructField("date", StringType(), False),
        StructField("grid_row", IntegerType(), False),
        StructField("grid_col", IntegerType(), False),
        StructField("latitude", DoubleType(), False),
        StructField("longitude", DoubleType(), False),
        StructField("rainfall_mm", DoubleType(), False),
    ])

    elevation_schema = StructType([
        StructField("grid_row", IntegerType(), False),
        StructField("grid_col", IntegerType(), False),
        StructField("latitude", DoubleType(), False),
        StructField("longitude", DoubleType(), False),
        StructField("elevation_valid_pixels", LongType(), False),
        StructField("elevation_missing_pixels", LongType(), False),
        StructField("elevation_mean", DoubleType(), True),
        StructField("elevation_min", DoubleType(), True),
        StructField("elevation_max", DoubleType(), True),
    ])

    rainfall_df = spark.createDataFrame(
        rainfall_records, schema=rainfall_schema
    )

    elevation_df = spark.createDataFrame(
        elevation_records, schema=elevation_schema
    )

    # Elevation statistics are shared across the four rainfall dates.
    combined_df = rainfall_df.join(
        elevation_df.drop("latitude", "longitude"),
        on=["grid_row", "grid_col"],
        how="left",
    )

    combined_df = combined_df.withColumn(
        "rainfall_date",
        F.to_date("date")
    )

    combined_df.groupBy("date").agg(
        F.count("*").alias("grid_cells"),
        F.avg("rainfall_mm").alias("mean_rainfall_mm"),
        F.max("rainfall_mm").alias("max_rainfall_mm"),
    ).orderBy("date").show(truncate=False)

    print("Combined records:", combined_df.count())

    # Spark writes a directory containing part files.
    OUTPUT_DIR.parent.mkdir(parents=True, exist_ok=True)

    combined_df.drop("rainfall_date").write \
        .mode("overwrite") \
        .option("header", True) \
        .csv(str(OUTPUT_DIR))

    print("Output saved to:", OUTPUT_DIR)

    spark.stop()


if __name__ == "__main__":
    main()
