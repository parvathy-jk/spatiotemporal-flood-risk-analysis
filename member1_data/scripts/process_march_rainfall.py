from pathlib import Path
import json
import numpy as np
import rasterio
from rasterio.windows import from_bounds

BASE = Path("member1_data/data")
INPUT_DIR = BASE / "processed/march_2025/rainfall_daily_accum"
OUTPUT_DIR = BASE / "processed/march_2025/rainfall_kerala"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WEST, SOUTH, EAST, NORTH = 74.0, 8.0, 78.0, 13.0
FILL_VALUE = 29999
NODATA = -9999.0
SCALE_DIVISOR = 10.0

files = sorted(INPUT_DIR.glob("*.total.accum.tif"))

if len(files) != 4:
    raise SystemExit(
        f"Expected 4 daily total.accum TIFFs; found {len(files)} in {INPUT_DIR}"
    )

manifest = {
    "source_product": "NASA GPM IMERG daily GIS V07B",
    "variable": "total.accum",
    "dates": [],
    "source_units": "Stored integer values in tenths of a millimetre",
    "processed_units": "mm",
    "scale_conversion": "Valid stored values divided by 10",
    "fill_value": FILL_VALUE,
    "fill_value_handling": "Excluded before scale conversion; output NoData is -9999",
    "study_extent": {
        "west": WEST,
        "south": SOUTH,
        "east": EAST,
        "north": NORTH,
        "note": "Rectangular bounding box; not an exact Kerala state boundary"
    },
    "outputs": []
}

for source_path in files:
    date = source_path.name.split(".3IMERG.")[1][:8]
    output_path = OUTPUT_DIR / f"rainfall_{date}_kerala_mm.tif"

    with rasterio.open(source_path) as src:
        if src.crs is None or src.crs.to_epsg() != 4326:
            raise ValueError(f"Expected EPSG:4326: {source_path.name}")

        window = from_bounds(
            WEST, SOUTH, EAST, NORTH, transform=src.transform
        ).round_offsets().round_lengths()

        raw = src.read(1, window=window)
        transform = src.window_transform(window)

        # NASA's documented fill value must not be treated as rainfall.
        valid = raw != FILL_VALUE
        valid &= raw <= 29998

        rainfall = np.full(raw.shape, NODATA, dtype=np.float32)
        rainfall[valid] = raw[valid].astype(np.float32) / SCALE_DIVISOR

        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            height=rainfall.shape[0],
            width=rainfall.shape[1],
            transform=transform,
            dtype="float32",
            count=1,
            nodata=NODATA,
            compress="deflate"
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(rainfall, 1)
            dst.update_tags(
                source_product="NASA GPM IMERG daily GIS V07B",
                variable="total.accum",
                date=date,
                units="mm",
                scale_conversion="stored value divided by 10",
                source_fill_value=str(FILL_VALUE),
                output_nodata=str(NODATA)
            )

    valid_values = rainfall[rainfall != NODATA]
    item = {
        "date": f"{date[:4]}-{date[4:6]}-{date[6:8]}",
        "source_file": source_path.name,
        "output_file": str(output_path),
        "width": int(rainfall.shape[1]),
        "height": int(rainfall.shape[0]),
        "valid_pixels": int(valid_values.size),
        "missing_pixels": int(np.count_nonzero(rainfall == NODATA)),
        "units": "mm"
    }

    if valid_values.size:
        item["minimum_mm"] = float(valid_values.min())
        item["maximum_mm"] = float(valid_values.max())
        item["mean_mm"] = float(valid_values.mean())

    manifest["dates"].append(item["date"])
    manifest["outputs"].append(item)

    print(f"\nProcessed: {source_path.name}")
    print(f"Output: {output_path}")
    print(f"Dimensions: {rainfall.shape[1]} x {rainfall.shape[0]}")
    print(f"Valid pixels: {item['valid_pixels']}")
    print(f"Missing pixels: {item['missing_pixels']}")
    if valid_values.size:
        print(f"Minimum rainfall: {item['minimum_mm']:.2f} mm")
        print(f"Maximum rainfall: {item['maximum_mm']:.2f} mm")
        print(f"Mean rainfall: {item['mean_mm']:.2f} mm")

manifest_path = BASE / "processed/march_2025/rainfall_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

print(f"\nManifest saved: {manifest_path}")
print(f"Completed {len(manifest['outputs'])} daily rainfall rasters.")
