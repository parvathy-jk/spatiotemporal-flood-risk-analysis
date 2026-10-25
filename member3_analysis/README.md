# Member 3: Data Analysis and Visualization

## 1. Overview

Member 3 is responsible for analyzing the processed river water-level, rainfall, and elevation datasets; identifying trends and potential risk indicators; generating visualizations; and producing a preliminary combined risk assessment for the Spatiotemporal Flood Risk Analysis project.

The analysis uses processed data prepared by the other project components. It provides exploratory insights into river conditions, rainfall patterns, terrain characteristics, and areas that may warrant further investigation for flood risk.

**Important:** The current combined risk index is exploratory. It is not a validated flood prediction model, and its scores should not be interpreted as flood probabilities.

## 2. Responsibilities

Member 3's responsibilities include:

- Analyzing cleaned river water-level observations.
- Examining rainfall patterns over the selected observation period.
- Inspecting elevation data and identifying potential data-quality issues.
- Combining rainfall and elevation information to calculate a preliminary risk index.
- Producing charts and visualizations to communicate findings.
- Generating analysis outputs for further evaluation and project reporting.
- Documenting limitations, assumptions, and possible improvements.

## 3. Dataset Overview

### 3.1 River Water-Level Data

**Processed file:**
`member1_data/data/processed/river_clean.csv`

The cleaned river dataset contains:

- **Records:** 465,076
- **Stations:** 26
- **Districts:** 9
- **Overall date range:** May 29, 2021 – March 10, 2025

The analysis examines river water-level trends across stations and districts. It also identifies stations with relatively high observed water levels.

A high relative water level is an indicator for further investigation, not conclusive evidence that flooding occurred.

### 3.2 Rainfall Data

**Processed directory:**
`member1_data/data/processed/rainfall_kerala/`

**Rainfall manifest:**
`member1_data/data/processed/rainfall_manifest.json`

The rainfall dataset contains 14 daily NASA GPM IMERG V07B rasters covering:

**September 21 – October 4, 2024**

Each Kerala-cropped raster has a grid of 40 rows by 50 columns, giving 2,000 grid cells per day.

The rainfall/elevation analysis output contains 28,000 records, corresponding to 2,000 grid cells over 14 days.

Rainfall analysis focuses on daily patterns, high-rainfall observations, and spatial variations across the available grid.

### 3.3 Elevation Data

**Processed file:**
`member1_data/data/processed/elevation/elevation_kerala_bbox.tif`

The elevation raster covers the project's Kerala bounding box. It is used to examine terrain characteristics and contribute an elevation-related component to the preliminary risk assessment.

Elevation data-quality checks include examining valid pixels, NoData values, and the distribution of elevation values.

Zero-valued elevation pixels should not automatically be treated as missing data without additional validation.

## 4. Analysis Modules

The analysis scripts are located in:

`member3_analysis/analysis/`

### 4.1 River Analysis

**Command:**

```bash
python -m member3_analysis.analysis.river_analysis
```

This module analyzes the cleaned river dataset and produces a summary of river observations, stations, and districts.

Reported results include:

- 12,648 river daily-summary records.
- 26 river stations.
- 9 districts.
- 2 stations flagged for high relative water levels.

**Output:**

`member3_analysis/analysis/output/river_analysis.json`

### 4.2 Rainfall Analysis

**Command:**

```bash
python -m member3_analysis.analysis.rainfall_analysis
```

This module examines the rainfall/elevation records for the selected 14-day period. It identifies high-rainfall observations and summarizes rainfall patterns.

Reported results include:

- 28,000 rainfall/elevation records.
- 14 days of rainfall observations.
- Daily maximum grid-cell rainfall values of at least 100 mm on two dates:
  - September 29, 2024: 107.10 mm.
  - October 4, 2024: 102.00 mm.

These are maximum values for individual grid cells, not averages over all of Kerala.

**Output:**

`member3_analysis/analysis/output/rainfall_analysis.json`

### 4.3 Combined Risk Assessment

**Command:**

```bash
python -m member3_analysis.analysis.combined_analysis
```

The combined analysis brings together rainfall and elevation information to calculate an exploratory risk index.

The current analysis reported 1,440 grid cells with calculated risk scores.

The preliminary index is intended to support exploratory screening and visualization. Its weights have not been calibrated against verified flood observations, and the output is not a probability of flooding.

River water-level analysis is currently performed separately. The combined rainfall/elevation index should not be interpreted as incorporating validated river-based flood predictions.

**Output:**

`member3_analysis/analysis/output/combined_risk_assessment.json`

## 5. Visualizations

Visualization scripts are located in:

`member3_analysis/visualization/`

Generated images are stored in:

`member3_analysis/visualization/output/`

The current visualization outputs include:

| Visualization | Purpose |
|---|---|
| `district_average_water_level.png` | Compares average river water levels across districts. |
| `district_maximum_water_level.png` | Compares maximum observed river water levels across districts. |
| `high_relative_river_stations.png` | Highlights stations flagged for high relative water levels. |
| `daily_rainfall_trends.png` | Shows rainfall changes during the selected observation period. |
| `top_10_rainfall_cells.png` | Displays the highest rainfall observations among selected grid cells. |
| `elevation_data_quality.png` | Examines elevation data characteristics and quality. |
| `rainfall_screening_threshold.png` | Visualizes the rainfall screening threshold. |
| `rainfall_grid_heatmap.png` | Displays rainfall values across grid indices. |
| `combined_risk_dashboard.png` | Presents a summary of the combined analysis. |
| `preliminary_risk_heatmap.png` | Visualizes the exploratory rainfall/elevation risk scores. |
| `preliminary_risk_top10.png` | Displays the highest-scoring grid cells. |
| `rainfall_vs_preliminary_risk.png` | Examines the relationship between rainfall and preliminary risk scores. |

**Visualization limitation:** The rainfall grid heatmap and preliminary risk heatmap use grid indices. They should not be presented as geographically verified flood-risk maps without validating the spatial alignment and mapping of grid cells to geographic coordinates.

## 6. Observation Period and Data Limitations

The datasets cover different overall periods:

- **River water-level data:** May 29, 2021 – March 10, 2025.
- **Rainfall/elevation grid:** September 21 – October 4, 2024.

The rainfall observation period falls within the overall date range of the river dataset. However, the overall date ranges alone do not establish how many river observations overlap with the rainfall period. The actual river records for these dates must be checked before performing date-specific comparisons.

Other limitations include:

1. **Spatial alignment:** The rainfall and elevation rasters have different resolutions. Although their dimensions have a 120:1 ratio, exact grid alignment has not been fully verified.
2. **Risk-score calibration:** The preliminary risk index uses uncalibrated weights and has not been validated against verified flood events.
3. **Elevation quality:** Zero-valued elevation pixels and missing values require careful interpretation


## Random Forest Preliminary Flood-Risk Screening

### Overview
A Random Forest classifier was implemented to classify rainfall grid cells into Low, Medium, and High preliminary risk categories. The analysis combines rainfall and elevation characteristics from the September–October 2024 study period.

The classifier learns to reproduce categories generated by a heuristic screening score. These categories are intended for preliminary screening and do not represent verified flood events or calibrated flood probabilities.

### Input Features
The model uses five features:

- `rainfall_mean_mm` — mean rainfall per grid cell over the study period.
- `elevation_mean` — mean elevation.
- `elevation_min` — minimum elevation statistic.
- `elevation_max` — maximum elevation statistic.
- `elevation_coverage` — proportion of valid elevation pixels.

### Dataset and Validation
- Usable grid cells: 1,440
- Training samples: 1,316
- Testing samples: 124
- Validation method: spatial holdout using grid rows 26–29 for testing.
- Categories: Low, Medium, and High.

### Evaluation Results

| Metric | Result |
|---|---:|
| Accuracy | 93.55% |
| Macro F1-score | 92.73% |

#### Per-class performance

| Category | Precision | Recall | F1-score | Test samples |
|---|---:|---:|---:|---:|
| Low | 82.61% | 95.00% | 88.37% | 20 |
| Medium | 98.44% | 90.00% | 94.03% | 70 |
| High | 91.89% | 100.00% | 95.77% | 34 |

These results measure how well the model reproduces the heuristic screening categories on the selected spatial holdout. They do not establish its accuracy at predicting real flood events.

### Feature Importance

The leading features reported by the fitted model were:

| Feature | Importance |
|---|---:|
| Mean rainfall | 37.86% |
| Mean elevation | 31.10% |
| Maximum elevation | 21.21% |
| Minimum elevation | 9.47% |
| Elevation coverage | 0.36% |

Rainfall mean and elevation-related features account for most of the model's reported feature importance.

### Outputs

The analysis saves its generated files under `member3_analysis/analysis/output/random_forest/`:

- `model_metrics.json` — evaluation metrics and classification report.
- `confusion_matrix.png` — classification confusion matrix.
- `feature_importance.csv` — feature-importance values.
- `feature_importance.png` — feature-importance visualization.
- `risk_classifications.csv` — grid-cell screening categories and model predictions.
- `random_forest_model.joblib` — saved trained model.

The risk-map visualization is saved as `member3_analysis/visualization/output/random_forest_risk_map.png`.

### Limitations

- Target categories are derived from a heuristic screening score rather than verified flood labels.
- Model evaluation measures reproduction of those categories, not real-world flood-prediction performance.
- The evaluation uses one spatial holdout; performance may differ in other geographic areas.
- The screening score is not a flood probability.
- Spatial alignment and elevation-data quality require further validation.