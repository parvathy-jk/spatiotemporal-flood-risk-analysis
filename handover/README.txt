MEMBER 2 - PROCESSED OUTPUTS HANDOVER
=====================================

1. river_daily_summary.tsv
   Hadoop MapReduce output summarising river water-level observations
   by station and date. This is the existing processed river dataset.

2. spark_rainfall_elevation.csv
   Original Apache Spark output for rainfall data dated August 1-4, 2025,
   joined with elevation statistics by rainfall grid cell.

3. spark_rainfall_elevation_march_2025.csv
   Updated Apache Spark output for rainfall data dated March 1-4, 2025,
   joined with elevation statistics by rainfall grid cell.
   Contains 8,000 records: 2,000 grid cells for each of four dates.

PROCESSING DETAILS
------------------
The March output was generated using Apache Spark 3.5.9 through PySpark.
The rainfall grid is 40 x 50 cells. Elevation statistics were aggregated
from corresponding 120 x 120 blocks of the elevation raster.

March daily rainfall statistics:
Date         Mean rainfall (mm)    Maximum rainfall (mm)
2025-03-01   2.78985               42.6
2025-03-02   5.42660               78.9
2025-03-03   1.19335               53.8
2025-03-04   0.58230                7.3

IMPORTANT DATA LIMITATION
-------------------------
The river dataset contains no observations for March 1-4, 2025.
Although it includes observations on March 9-10, those dates do not
overlap with the four March rainfall dates processed here.

Therefore, these outputs support rainfall-elevation processing and
river water-level summaries, but do not establish a direct,
date-matched rainfall-river relationship for March 1-4.

The August rainfall dates also do not overlap with the river observations
in the current dataset. Do not interpret the separate outputs as a
direct rainfall-river comparison without matching dates.

END OF HANDOVER
