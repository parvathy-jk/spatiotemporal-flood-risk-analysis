# HDFS Storage and Data Upload

## Project
**Spatiotemporal Flood Risk Analysis Using Big Data**

## Environment
- Operating system: Ubuntu
- Hadoop version: 3.5.0
- Deployment: Single-node HDFS

## HDFS Base Path

`/user/lakshmi/flood-risk-analysis`

## Directory Structure

```text
/user/lakshmi/flood-risk-analysis/
├── river/
├── rainfall/
├── elevation/
└── metadata/
```

## Current Dataset

The project currently uses rainfall data covering **September 21–October 4, 2024**, comprising 14 daily NASA GPM IMERG V07B rainfall rasters.

### Local Data Locations

| Dataset | Location |
|---|---|
| Raw rainfall archives | `member1_data/data/raw/rainfall/` |
| Extracted rainfall rasters | `member1_data/data/processed/rainfall_tiffs/` |
| Kerala-cropped rainfall rasters | `member1_data/data/processed/rainfall_kerala/` |
| Raw river data | `member1_data/data/raw/river/river.csv` |
| Cleaned river data | `member1_data/data/processed/river_clean.csv` |
| Processed elevation raster | `member1_data/data/processed/elevation/elevation_kerala_bbox.tif` |
| Rainfall manifest | `member1_data/data/processed/rainfall_manifest.json` |

## HDFS Storage Layout

The intended HDFS layout is:

- **River data:** `/user/lakshmi/flood-risk-analysis/river/`
- **Rainfall data:** `/user/lakshmi/flood-risk-analysis/rainfall/`
- **Elevation data:** `/user/lakshmi/flood-risk-analysis/elevation/`
- **Metadata:** `/user/lakshmi/flood-risk-analysis/metadata/`

These paths describe the planned directory structure. Verify the contents of HDFS before assuming that the current dataset has been uploaded.

## Rainfall Preprocessing

The rainfall processing workflow consists of:

1. Extracting the daily rainfall GeoTIFFs from the downloaded ZIP archives.
2. Processing the rainfall rasters.
3. Cropping the rasters to the study area's rectangular geographic extent.
4. Validating the output raster dimensions, coordinate reference system, rainfall values, and NoData handling.
5. Generating a manifest describing the processed rainfall data.

Relevant scripts:

- `member1_data/scripts/process_rainfall.py`
- `member1_data/scripts/crop_rainfall_kerala.py`
- `member1_data/scripts/validate_processed_data.py`

## Geographic and Data Limitations

- The study extent is a rectangular bounding box covering approximately 74°E–78°E and 8°N–13°N, not the exact Kerala state boundary.
- The rainfall dataset covers only 14 days.
- River observations span a longer period and contain temporal gaps at some stations.
- Elevation coverage and raster alignment should be verified before interpreting combined rainfall–elevation results.
- The datasets must be temporally and spatially compatible before being used to train or validate a flood-risk prediction model.