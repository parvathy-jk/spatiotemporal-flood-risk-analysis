from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge

RAW_DIR = Path("member1_data/data/raw/elevation")
OUT_DIR = Path("member1_data/data/processed/elevation")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Approximate Kerala-region bounding box
WEST, SOUTH, EAST, NORTH = 74, 8, 78, 13

files = sorted(RAW_DIR.glob("*.tif"))

if not files:
    raise FileNotFoundError("No elevation TIFF files found.")

sources = []

try:
    for file in files:
        sources.append(rasterio.open(file))

    # All source tiles should use the same CRS.
    crs_list = {str(src.crs) for src in sources}
    if len(crs_list) != 1:
        raise ValueError(f"Source tiles use different CRS values: {crs_list}")

    # Merge the tiles and crop to the requested bounds.
    mosaic, transform = merge(
        sources,
        bounds=(WEST, SOUTH, EAST, NORTH),
        nodata=-9999.0,
        dtype="float32"
    )

    output = OUT_DIR / "elevation_kerala_bbox.tif"

    profile = sources[0].profile.copy()
    profile.update(
        driver="GTiff",
        height=mosaic.shape[1],
        width=mosaic.shape[2],
        count=1,
        dtype="float32",
        transform=transform,
        nodata=-9999.0,
        compress="deflate"
    )

    with rasterio.open(output, "w", **profile) as dst:
        dst.write(mosaic)
        dst.update_tags(
            units="metres",
            source="Copernicus DSM",
            region="Approximate Kerala bounding box",
            nodata_note="Output gaps use -9999; source zero and negative values retained"
        )

    # Exclude only the output's explicit no-data value.
    data = mosaic[0]
    valid = np.isfinite(data) & (data != -9999.0)

    print("Input tiles:", len(files))
    print("Output file:", output)
    print("CRS:", sources[0].crs)
    print("Dimensions:", data.shape)
    print("Valid pixels:", int(valid.sum()))
    print("No-data pixels:", int((~valid).sum()))

    if valid.any():
        print("Minimum elevation (m):", float(data[valid].min()))
        print("Maximum elevation (m):", float(data[valid].max()))

finally:
    for src in sources:
        src.close()
