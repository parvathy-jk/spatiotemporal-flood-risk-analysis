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
