from pathlib import Path
import rasterio

folder = Path("member1_data/data/raw/elevation")
files = sorted(folder.glob("*.tif"))

print("Total elevation files:", len(files))

for file in files:
    print("\nFile:", file.name)

    try:
        with rasterio.open(file) as src:
            print("CRS:", src.crs)
            print("Dimensions:", src.width, "x", src.height)
            print("Bounds:", src.bounds)
            print("Resolution:", src.res)
            print("Data type:", src.dtypes[0])
            print("No-data value:", src.nodata)

            elevation = src.read(1, masked=True)

            if elevation.count() > 0:
                print("Minimum elevation:", float(elevation.min()), "m")
                print("Maximum elevation:", float(elevation.max()), "m")
                print("Valid pixels:", int(elevation.count()))
            else:
                print("No valid elevation pixels found.")

    except Exception as error:
        print("Error reading file:", error)
