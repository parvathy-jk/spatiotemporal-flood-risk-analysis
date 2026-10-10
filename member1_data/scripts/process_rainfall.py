from pathlib import Path
import zipfile
import json


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "data" / "raw" / "rainfall"

OUTPUT_DIR = BASE_DIR / "data" / "processed" / "rainfall_tiffs"

MANIFEST_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "rainfall_manifest.json"
)


def process_rainfall():
    """Extract candidate total accumulated precipitation TIFFs."""

    print("=" * 60)
    print("NASA IMERG RAINFALL DATA PREPARATION")
    print("=" * 60)

    zip_files = sorted(INPUT_DIR.glob("*.zip"))

    print("Input folder:", INPUT_DIR)
    print("ZIP files found:", len(zip_files))

    if not zip_files:
        raise FileNotFoundError(
            f"No rainfall ZIP files found in {INPUT_DIR}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []

    for zip_path in zip_files:
        print("\nInspecting:", zip_path.name)

        try:
            with zipfile.ZipFile(zip_path, "r") as archive:

                candidates = [
                    name
                    for name in archive.namelist()
                    if name.lower().endswith(".total.accum.tif")
                ]

                if not candidates:
                    print("No total.accum.tif file found.")
                    continue

                for member in candidates:
                    output_name = Path(member).name
                    output_path = OUTPUT_DIR / output_name

                    # Extract only the selected TIFF.
                    with archive.open(member) as source:
                        with output_path.open("wb") as destination:
                            destination.write(source.read())

                    print("Extracted:", output_name)
                    print(
                        "Size (bytes):",
                        output_path.stat().st_size
                    )

                    manifest.append({
                        "source_archive": zip_path.name,
                        "source_member": member,
                        "output_file": output_name,
                        "size_bytes": output_path.stat().st_size,
                        "measurement": "total accumulated precipitation",
                        "units": "not yet verified"
                    })

        except zipfile.BadZipFile:
            print("WARNING: Invalid ZIP archive:", zip_path.name)

    with MANIFEST_FILE.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4)

    print("\nProcessing complete.")
    print("Extracted TIFF count:", len(manifest))
    print("Output folder:", OUTPUT_DIR)
    print("Manifest:", MANIFEST_FILE)


if __name__ == "__main__":
    process_rainfall()
