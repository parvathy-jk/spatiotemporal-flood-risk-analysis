import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path("member1_data/data/processed")
report = {}

# 1. River water-level data
river_path = ROOT / "river_clean.csv"
river = pd.read_csv(river_path)

time_col = "Data Acquisition Time"
level_col = "River Water Level Telemetry Hourly (meter)"
station_col = "Station"

times = pd.to_datetime(
    river[time_col],
    format="%d-%m-%Y %H:%M",
    errors="coerce"
)
levels = pd.to_numeric(river[level_col], errors="coerce")

station_times = pd.DataFrame({
    "station": river[station_col],
    "time": times
}).dropna()

duplicate_station_times = int(
    station_times.duplicated(["station", "time"]).sum()
)

valid_times = station_times.groupby("station")["time"].agg(
    ["min", "max", "count"]
)

report["river"] = {
    "file": str(river_path),
    "rows": int(len(river)),
    "columns": int(len(river.columns)),
    "missing_cells": int(river.isna().sum().sum()),
    "invalid_timestamps": int(times.isna().sum()),
    "invalid_water_levels": int(levels.isna().sum()),
    "duplicate_station_timestamps": duplicate_station_times,
    "unique_stations": int(river[station_col].nunique()),
    "water_level_min_m": float(levels.min()),
    "water_level_max_m": float(levels.max()),
    "water_level_mean_m": float(levels.mean()),
    "station_time_ranges": int(len(valid_times)),
}

# 2. Processed rainfall rasters
rainfall_dir = ROOT / "rainfall_kerala"
rainfall_files = sorted(rainfall_dir.glob("*.tif"))
rainfall_report = []

for path in rainfall_files:
    with rasterio.open(path) as ds:
        values = ds.read(1, masked=True)
        valid = values.compressed()

        rainfall_report.append({
            "file": path.name,
            "crs": str(ds.crs),
            "width": int(ds.width),
            "height": int(ds.height),
            "units": ds.tags().get("units", "not recorded"),
            "nodata": ds.nodata,
            "valid_pixels": int(valid.size),
            "missing_pixels": int(values.size - valid.size),
            "minimum_mm": float(valid.min()) if valid.size else None,
            "maximum_mm": float(valid.max()) if valid.size else None,
            "mean_mm": float(valid.mean()) if valid.size else None,
            "nonfinite_valid_values": int(
                np.count_nonzero(~np.isfinite(valid))
            ),
            "negative_valid_values": int(np.count_nonzero(valid < 0)),
        })

report["rainfall"] = {
    "files_found": len(rainfall_files),
    "rasters": rainfall_report,
}

# 3. Elevation mosaic
elevation_path = ROOT / "elevation" / "elevation_kerala_bbox.tif"

with rasterio.open(elevation_path) as ds:
    elevation = ds.read(1, masked=True)
    valid = elevation.compressed()

    report["elevation"] = {
        "file": str(elevation_path),
        "crs": str(ds.crs),
        "width": int(ds.width),
        "height": int(ds.height),
        "bounds": list(ds.bounds),
        "resolution": list(ds.res),
        "nodata": ds.nodata,
        "valid_pixels": int(valid.size),
        "missing_pixels": int(elevation.size - valid.size),
        "missing_percent": round(
            100 * (elevation.size - valid.size) / elevation.size, 2
        ),
        "minimum_m": float(valid.min()) if valid.size else None,
        "maximum_m": float(valid.max()) if valid.size else None,
        "mean_m": float(valid.mean()) if valid.size else None,
        "nonfinite_valid_values": int(
            np.count_nonzero(~np.isfinite(valid))
        ),
    }

# Save report
report_path = ROOT / "validation_report.json"
report_path.write_text(json.dumps(report, indent=2))

print("Validation finished.")
print("River rows:", report["river"]["rows"])
print("River stations:", report["river"]["unique_stations"])
print("Duplicate station/timestamp records:",
      report["river"]["duplicate_station_timestamps"])
print("Rainfall rasters:", report["rainfall"]["files_found"])
print("Elevation missing pixels:",
      report["elevation"]["missing_percent"], "%")
print("Report saved to:", report_path)
