#!/usr/bin/env python3

import sys


def main():
    current_key = None

    count = 0
    total = 0.0
    minimum = float("inf")
    maximum = float("-inf")

    latitude = None
    longitude = None

    def emit_result(key, n, total_value, low, high, lat, lon):
        if key is None or n == 0:
            return

        station, district, date = key.split("|", 2)

        average = total_value / n

        # Output columns are tab-separated.
        print(
            f"{station}\t{district}\t{date}\t"
            f"{n}\t{average:.4f}\t{low:.4f}\t"
            f"{high:.4f}\t{lat}\t{lon}"
        )

    for line in sys.stdin:
        line = line.rstrip("\n")

        if not line:
            continue

        try:
            key, value = line.split("\t", 1)

            fields = value.split(",")

            n = int(fields[0])
            total_value = float(fields[1])
            low = float(fields[2])
            high = float(fields[3])
            lat = float(fields[4])
            lon = float(fields[5])

        except (ValueError, IndexError):
            continue

        if key != current_key:
            emit_result(
                current_key,
                count,
                total,
                minimum,
                maximum,
                latitude,
                longitude
            )

            current_key = key

            count = 0
            total = 0.0
            minimum = float("inf")
            maximum = float("-inf")

            latitude = lat
            longitude = lon

        count += n
        total += total_value

        minimum = min(minimum, low)
        maximum = max(maximum, high)

    # Emit the final group.
    emit_result(
        current_key,
        count,
        total,
        minimum,
        maximum,
        latitude,
        longitude
    )


if __name__ == "__main__":
    main()
