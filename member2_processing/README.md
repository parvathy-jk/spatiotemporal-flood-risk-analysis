# Niya: Big Data Processing

## 1. Objective
Process historical river observations using Hadoop MapReduce and analyze rainfall and elevation using Apache Spark.

## 2. Technology Stack
- Python
- Hadoop 3.3.6
- HDFS and Hadoop Streaming
- Apache Spark 3.5.9
- Rasterio, NumPy and Pandas
- GeoTIFF and CSV

Spark runs in local mode on a single machine.

## 3. Hadoop MapReduce

### Input
HDFS: `/user/niya/flood-risk-analysis/input/river/river_clean.csv`

Total observations: 465,076.

### Mapper
File: `mapreduce/mapper.py`

Extracts station, district, date, water level, latitude and longitude. Groups observations by station, district and date.

### Reducer
File: `mapreduce/reducer.py`

Calculates observation count, average water level, minimum and maximum water levels.

### Output
HDFS: `/user/niya/flood-risk-analysis/output/river_daily_summary/`

Local: `results/mapreduce/river_daily_summary.tsv`

Total daily station summaries: 12,648.

## 4. Apache Spark

Script: `spark/process_rainfall_elevation.py`

Inputs:
- Four daily rainfall GeoTIFF files for August 1–4, 2025.
- Elevation GeoTIFF.

Processing:
1. Read rainfall and elevation rasters.
2. Calculate elevation statistics for 120 x 120 pixel blocks.
3. Create Spark DataFrames.
4. Join rainfall and elevation by grid row and column.
5. Calculate daily rainfall summaries.
6. Export the results to CSV.

Output: `results/spark/rainfall_elevation/`

Total records: 8,000, representing 2,000 grid cells over four days.

| Date | Mean rainfall (mm) | Maximum rainfall (mm) |
|---|---:|---:|
| 2025-08-01 | 15.8765 | 79.2 |
| 2025-08-02 | 16.85365 | 90.7 |
| 2025-08-03 | 23.9636 | 122.7 |
| 2025-08-04 | 13.1508 | 144.0 |

## 5. Data Quality and Limitations

River observations range from May 29, 2021, to March 10, 2025. Rainfall data covers August 1–4, 2025. No river observations exist for those rainfall dates, so direct same-date analysis is not possible.

The elevation raster contains 28,800,000 pixels, of which 8,644,800 (30.02%) are missing.

Of the 2,000 rainfall-grid cells:
- 560 have entirely missing elevation.
- 119 have partially missing elevation.
- 1,321 have complete elevation coverage.

Missing elevation must not be interpreted as zero. Some valid zero-valued pixels require further investigation.

The rainfall and elevation grids have slightly different origins. The current implementation uses fixed 120 x 120 elevation blocks, so spatial alignment should be considered before detailed geographical interpretation.

These pipelines perform data processing and descriptive analysis. They do not constitute a validated flood prediction model.

## 6. Reproduction

Run commands from the project root with the Python environment activated.

Spark:
` spark-submit member2_processing/spark/process_rainfall_elevation.py `

Hadoop MapReduce requires HDFS and YARN to be running and the input dataset to be available in HDFS. The output directory must not already exist when rerunning the job.
