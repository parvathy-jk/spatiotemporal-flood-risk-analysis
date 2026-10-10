
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds

INPUT_DIR = Path("member1_data/data/processed/rainfall_tiffs")
OUTPUT_DIR = Path("member1_data/data/processed/rainfall_kerala")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WEST, SOUTH, EAST, NORTH = 74, 8, 78, 13
FILL_VALUE = 29999
NODATA_OUT = -9999.0

for input_file in sorted(INPUT_DIR.glob("*.tif")):
    with rasterio.open(input_file) as src:
        window = from_bounds(
            WEST, SOUTH, EAST, NORTH,
            transform=src.transform
        ).round_offsets().round_lengths()

        raw = src.read(1, window=window)

        # Mask NASA's documented missing-data code.
        missing = raw == FILL_VALUE

        # Convert valid stored values from tenths of mm to mm.
        rainfall_mm = raw.astype(np.float32) / 10.0
        rainfall_mm[missing] = NODATA_OUT

        output_file = OUTPUT_DIR / (
            input_file.stem + "_kerala_mm.tif"
        )

        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            height=rainfall_mm.shape[0],
            width=rainfall_mm.shape[1],
            count=1,
            dtype="float32",
            transform=src.window_transform(window),
            nodata=NODATA_OUT,
            compress="deflate"
        )

        with rasterio.open(output_file, "w", **profile) as dst:
            dst.write(rainfall_mm, 1)
            dst.update_tags(
                units="mm",
                fill_value_handled=str(FILL_VALUE),
                scale_applied="divide_by_10",
                region="Approximate Kerala bounding box"
            )

        valid = rainfall_mm != NODATA_OUT

        print("\nFile:", output_file.name)
        print("Missing pixels:", int(missing.sum()))
        print("Valid pixels:", int(valid.sum()))

        if valid.any():
            print("Mean rainfall (mm):",
                  round(float(rainfall_mm[valid].mean()), 2))
            print("Maximum rainfall (mm):",
                  round(float(rainfall_mm[valid].max()), 2))
