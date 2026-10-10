from pathlib import Path
import zipfile


def inspect_rainfall_archives():
    """
    Inspect NASA GPM IMERG rainfall ZIP archives.

    This script lists archive contents without modifying
    or extracting the original files.
    """

    rainfall_folder = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "raw"
        / "rainfall"
    )

    zip_files = sorted(rainfall_folder.glob("*.zip"))

    print("NASA GPM IMERG RAINFALL INSPECTION")
    print("=" * 45)
    print("Folder:", rainfall_folder)
    print("ZIP files found:", len(zip_files))

    if not zip_files:
        print("No rainfall ZIP files found.")
        print("Check the rainfall data folder.")
        return

    for file in zip_files:
        print("\nArchive:", file.name)
        print("Archive size (MB):", round(file.stat().st_size / (1024 * 1024), 2))

        try:
            with zipfile.ZipFile(file, "r") as archive:
                print("Files inside archive:")

                for item in archive.infolist():
                    if not item.is_dir():
                        print(
                            "  ",
                            item.filename,
                            "| Size:",
                            item.file_size,
                            "bytes"
                        )

        except zipfile.BadZipFile:
            print("WARNING: This is not a valid ZIP archive.")

        except OSError as error:
            print("Could not inspect archive:", error)


if __name__ == "__main__":
    inspect_rainfall_archives()
