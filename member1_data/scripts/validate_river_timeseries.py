import json
from pathlib import Path

import pandas as pd

ROOT = Path("member1_data/data/processed")
INPUT = ROOT / "river_clean.csv"
OUTPUT = ROOT / "river_timeseries_report.json"

df = pd.read_csv(INPUT)

station_col = "Station"
time_col = "Data Acquisition Time"
level_col = "River Water Level Telemetry Hourly (meter)"

df[time_col] = pd.to_datetime(
    df[time_col],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)
df[level_col] = pd.to_numeric(df[level_col], errors="coerce")

report = {
    "input_file": str(INPUT),
    "total_records": int(len(df)),
    "unique_stations": int(df[station_col].nunique()),
    "stations": []
}

for station, station_group in df.groupby(station_col):
    station_group = station_group.dropna(subset=[time_col]).copy()

    times = (
        station_group[time_col]
        .drop_duplicates()
        .sort_values()
    )
    gaps = times.diff().dropna()

    report["stations"].append({
        "station": str(station),
        "records": int(len(station_group)),
        "first_timestamp": (
            str(times.min()) if len(times) else None
        ),
        "last_timestamp": (
            str(times.max()) if len(times) else None
        ),
        "unique_timestamps": int(len(times)),
        "largest_gap_hours": (
            round(gaps.max().total_seconds() / 3600, 2)
            if len(gaps) else None
        ),
        "gaps_over_24_hours": int(
            (gaps > pd.Timedelta(hours=24)).sum()
        ),
        "gaps_over_7_days": int(
            (gaps > pd.Timedelta(days=7)).sum()
        ),
        "water_level_min_m": (
            float(station_group[level_col].min())
            if station_group[level_col].notna().any()
            else None
        ),
        "water_level_max_m": (
            float(station_group[level_col].max())
            if station_group[level_col].notna().any()
            else None
        )
    })

OUTPUT.write_text(json.dumps(report, indent=2) + "\n")

print("River time-series validation completed.")
print("Total records:", report["total_records"])
print("Unique stations:", report["unique_stations"])
print("Report saved to:", OUTPUT)
print("\nStation summary:")

for item in report["stations"]:
    print(
        f'{item["station"]}: '
        f'{item["records"]} records, '
        f'largest gap={item["largest_gap_hours"]} hours, '
        f'gaps >24 hours={item["gaps_over_24_hours"]}, '
        f'gaps >7 days={item["gaps_over_7_days"]}'
    )
