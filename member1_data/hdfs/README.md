# HDFS Storage and Data Upload

## Project
Spatiotemporal Flood Risk Analysis Using Big Data

## Environment
- Operating system: Ubuntu
- Hadoop version: 3.3.6
- Java version: OpenJDK 11
- Deployment: Single-node HDFS

## HDFS Base Path

/user/lakshmi/flood-risk-analysis

## Directory Structure

```text
/user/lakshmi/flood-risk-analysis/
├── river/
├── rainfall/
├── elevation/
└── metadata/
## March 2025 Rainfall Dataset

Four daily NASA GPM IMERG V07B rainfall rasters for March 1–4, 2025
were preprocessed and uploaded to HDFS.

### HDFS Paths

Processed rainfall rasters:
`/user/lakshmi/flood-risk-analysis/rainfall_march_2025/`

Rainfall processing manifest:
`/user/lakshmi/flood-risk-analysis/metadata/march_2025/rainfall_manifest.json`

### Processing

- Cropped to the bounding box: 74°E–78°E, 8°N–13°N.
- Converted valid source values to millimetres by dividing by 10.
- Source fill value: `29999`.
- Output NoData value: `-9999`.
- Coordinate reference system: EPSG:4326.

The study extent is a rectangular bounding box, not the exact Kerala state boundary.
