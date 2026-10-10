# Member 1 - Data Collection and Preprocessing

## Project

Spatiotemporal Flood Risk Analysis Using Big Data

## Responsibilities

Member 1 is responsible for collecting, inspecting, extracting, cleaning, and preprocessing rainfall, river water-level, and elevation datasets.

The prepared datasets support subsequent spatial analysis and big-data processing.

## Dataset Sources

### 1. Rainfall

- Source: NASA Global Precipitation Measurement (GPM) IMERG.
- Input format: ZIP archives containing GeoTIFF files.
- Sample period: 1–4 August 2025.
- Processing: Extract daily accumulated precipitation rasters, crop to a rectangular study area around Kerala, handle the documented fill value, and convert stored values to millimetres.
- Processed format: GeoTIFF.

### 2. River Water Level

- Source: National Water Data Portal dataset supplied for the project.
- Input format: CSV.
- Input file: `rwl_tel_hr_kerala_sw_999_2021_2025.csv`.
- Original records: 465,076.
- Columns: 23.
- Processing: Inspect fields, parse timestamps, validate numeric water levels and coordinates, check exact duplicate records, remove unusable rows if present, and sort by timestamp.
- Processed file: `river_clean.csv`.

### 3. Elevation

- Source: Copernicus Digital Elevation Model (DEM).
- Input format: GeoTIFF tiles.
- Processing: Inspect raster metadata, combine available tiles into a mosaic, and record missing coverage.
- Processed file: `elevation_kerala_bbox.tif`.

## Project Structure

```text
member1_data/
├── scripts/
├── data/
│   ├── raw/
│   │   ├── rainfall/
│   │   ├── river/
│   │   ├── elevation/
│   │   └── boundary/
│   └── processed/
└── README.md
## Validation Results

### Rainfall
- Source: NASA GPM IMERG daily precipitation product.
- Sample period: 1–4 August 2025.
- Four daily rainfall rasters were extracted and processed.
- The processed rasters use millimetres as their documented units.
- Fill-value handling and scale conversion are recorded in the rainfall manifest.
- The study area is a rectangular bounding box, not an exact Kerala state polygon.
- The four-day sample is intended for preprocessing demonstration and is not sufficient by itself for robust flood-risk modelling.

### River Water Level
- Original dataset contains 465,076 records and 23 columns.
- Cleaned dataset contains 465,076 records.
- No exact duplicate rows were detected during initial cleaning.
- No duplicate station/timestamp combinations were detected.
- Timestamp parsing and station-level temporal-gap analysis were performed.
- Some stations have gaps exceeding 24 hours and seven days.
- Temporal gaps are documented for downstream analysis rather than automatically filled.

### Elevation
- Fourteen Copernicus DEM tiles were combined into a raster mosaic.
- Output CRS: EPSG:4326.
- Mosaic extent: longitude 74–78 degrees E and latitude 8–13 degrees N.
- Approximately 30.02% of pixels in the rectangular mosaic are missing.
- Missing pixels have not been automatically replaced with zero.
- Elevation coverage requires further investigation before modelling.

### Validation Reports
- `data/processed/validation_report.json`
- `data/processed/river_timeseries_report.json`
- `data/processed/rainfall_manifest.json`

These generated reports are stored locally and excluded from Git along with processed datasets.

### Limitations
- Rainfall covers only four days.
- The rainfall crop is rectangular rather than clipped to the exact Kerala boundary.
- River observations contain substantial temporal gaps at some stations.
- Elevation coverage is incomplete.
- These limitations must be considered before combining the datasets for flood-risk analysis.
