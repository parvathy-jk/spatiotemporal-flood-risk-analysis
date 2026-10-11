# Niya: Big Data Processing

## 1. Objective

Process historical river observations using Hadoop MapReduce and
analyze rainfall and elevation data using Apache Spark.

## 2. Technology Stack

- Python
- Hadoop 3.3.6
- HDFS and Hadoop Streaming
- Apache Spark 3.5.9
- Rasterio, NumPy and Pandas
- GeoTIFF and CSV

Spark runs in local mode on a single machine.

## 3. Input Datasets

### River Observations

Local path:
`member1_data/data/processed/river_clean.csv`

HDFS path:
`/user/niya/flood-risk-analysis/input/river/river_clean.csv`

Number of observations: 465,076.

### Rainfall Data

Directory:
`member1_data/data/processed/rainfall_kerala/`

Contains four daily rainfall GeoTIFF files covering August 1–4, 2025.

### Elevation Data

File:
`member1_data/data/processed/elevation/elevation_kerala_bbox.tif`

## 4. Hadoop MapReduce

### Mapper

File: `member2_processing/mapreduce/mapper.py`

The mapper reads river observations and extracts station, district,
date, water level, latitude and longitude.

It groups observations using station, district and date as the key.

### Reducer

File: `member2_processing/mapreduce/reducer.py`

The reducer calculates the following daily station statistics:

- Number of observations
- Average water level
- Minimum water level
- Maximum water level

Latitude and longitude are also included in the output.

### Output

HDFS:
`/user/niya/flood-risk-analysis/output/river_daily_summary/`

Local:
`results/mapreduce/river_daily_summary.tsv`

The output contains 12,648 daily station summaries.

The output is tab-separated and contains nine columns:
station, district, date, count, average water level, minimum water level,
maximum water level, latitude and longitude.

## 5. Apache Spark Processing

Script:
`member2_processing/spark/process_rainfall_elevation.py`

### Processing Methodology

1. Read the four rainfall GeoTIFF files.
2. Read the elevation GeoTIFF.
3. Validate the coordinate reference systems, raster bounds and
   expected dimensions.
4. Aggregate elevation pixels into 120 x 120 pixel blocks.
5. Calculate elevation statistics for each rainfall grid cell.
6. Create Spark DataFrames for rainfall and elevation.
7. Join the DataFrames using grid row and column.
8. Calculate daily mean and maximum rainfall.
9. Export the combined records to CSV.

Spark executes in local mode using `local[*]`.

### Output

Directory:
`results/spark/rainfall_elevation/`

The output is a Spark CSV directory containing one or more part files
and a `_SUCCESS` marker.

The CSV includes rainfall date, grid coordinates, rainfall values,
elevation coverage counts and elevation statistics.

Total records: 8,000, representing 2,000 grid cells over four days.

### Daily Rainfall Summary

| Date | Mean rainfall (mm) | Maximum rainfall (mm) |
|---|---:|---:|
| 2025-08-01 | 15.8765 | 79.2 |
| 2025-08-02 | 16.85365 | 90.7 |
| 2025-08-03 | 23.9636 | 122.7 |
| 2025-08-04 | 13.1508 | 144.0 |

## 6. Data Quality and Limitations

River observations range from May 29, 2021, to March 10, 2025.
Rainfall data covers August 1–4, 2025.

No river observations exist for the rainfall dates. Therefore, the
current datasets do not support direct same-date river and rainfall
analysis.

The elevation raster contains 28,800,000 pixels, of which 8,644,800
(30.02%) are missing.

Of the 2,000 rainfall-grid cells:

- 560 have entirely missing elevation.
- 119 have partially missing elevation.
- 1,321 have complete elevation coverage.

Missing elevation must not be interpreted as zero. Valid zero-valued
pixels require separate consideration.

The rainfall and elevation grids have slightly different origins.
The current implementation uses fixed 120 x 120 elevation blocks.
Spatial alignment should therefore be considered before detailed
geographical interpretation.

These pipelines perform data processing and descriptive analysis.
They do not constitute a validated flood prediction model.

## 7. Reproduction

Run commands from the project root.

### Spark

Activate the Python environment and execute:

` spark-submit member2_processing/spark/process_rainfall_elevation.py `

The input datasets must be available at the paths listed in Section 3.
The script writes its output to `results/spark/rainfall_elevation/`.

### Hadoop MapReduce

Requirements:
- Hadoop 3.3.6 configured and running.
- HDFS and YARN services running.
- The river CSV uploaded to the HDFS input path.
- Hadoop Streaming JAR available.

Set the Streaming JAR path:

```bash
export STREAMING_JAR="$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar"
```

Ensure the HDFS input file exists:

```bash
hdfs dfs -ls /user/niya/flood-risk-analysis/input/river/river_clean.csv
```

Before rerunning the job, remove the previous output directory if it exists:

```bash
hdfs dfs -rm -r /user/niya/flood-risk-analysis/output/river_daily_summary
```

Run Hadoop Streaming from the project root:

```bash
hadoop jar "$STREAMING_JAR" \
  -files member2_processing/mapreduce/mapper.py,member2_processing/mapreduce/reducer.py \
  -mapper "python3 mapper.py" \
  -reducer "python3 reducer.py" \
  -input /user/niya/flood-risk-analysis/input/river/river_clean.csv \
  -output /user/niya/flood-risk-analysis/output/river_daily_summary
```

Verify successful completion:

```bash
hdfs dfs -test -e /user/niya/flood-risk-analysis/output/river_daily_summary/_SUCCESS \
  && echo "MapReduce SUCCESS" \
  || echo "MapReduce OUTPUT NOT VERIFIED"
```

Download the output:

```bash
mkdir -p results/mapreduce

hdfs dfs -get \
  /user/niya/flood-risk-analysis/output/river_daily_summary/part-00000 \
  results/mapreduce/river_daily_summary.tsv
```

The HDFS output directory is:
`/user/niya/flood-risk-analysis/output/river_daily_summary/`

The local output file is:
`results/mapreduce/river_daily_summary.tsv`

## 8. Integration Handover

The processed outputs are available locally at:

- `results/mapreduce/river_daily_summary.tsv`
- `results/spark/rainfall_elevation/`

These generated outputs are excluded from Git and are not automatically
available to other team members through the repository.

For downstream analysis, the MapReduce TSV and Spark CSV part file can
be read as tab-separated and comma-separated data, respectively.

The river and rainfall datasets cover different periods. Any combined
analysis must account for this temporal mismatch.
