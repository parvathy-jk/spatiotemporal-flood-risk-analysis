#!/usr/bin/env python3

import sys
import csv
from datetime import datetime


def main():
    reader = csv.reader(sys.stdin)

    for row in reader:
        try:
            # Ignore the CSV header.
            if not row or row[0].strip().lower() == "slno":
                continue

            # Expected column positions from the actual dataset.
            station = row[1].strip()
            district = row[6].strip()

            latitude = float(row[16])
            longitude = float(row[17])

            timestamp = datetime.strptime(
                row[21].strip(),
                "%Y-%m-%d %H:%M:%S"
            )

            water_level = float(row[22])

            # Reject incomplete or invalid records.
            if not station or not district:
                continue

            if not (
                -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                continue

            if water_level != water_level:
                continue

            date = timestamp.strftime("%Y-%m-%d")

            # Group records by station, district and date.
            key = f"{station}|{district}|{date}"

            # count, sum, minimum, maximum, latitude, longitude
            value = (
                f"1,{water_level},{water_level},"
                f"{water_level},{latitude},{longitude}"
            )

            print(f"{key}\t{value}")

        except (ValueError, IndexError):
            # Skip malformed records rather than crashing.
            continue


if __name__ == "__main__":
    main()
