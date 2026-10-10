from pathlib import Path
import pandas as pd

# Expected location of the original river dataset
DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "river"
    / "rwl_tel_hr_kerala_sw_999_2021_2025.csv"
)


def main():
    if not DATA_FILE.exists():
        print("River dataset has not been placed in:")
        print(DATA_FILE)
        print("\nDownload or copy the file into that folder first.")
        return

    # Read the CSV without modifying the original file
    df = pd.read_csv(DATA_FILE, low_memory=False)

    print("\n--- RIVER DATASET INSPECTION ---")
    print("File:", DATA_FILE.name)
    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nFirst five records:")
    print(df.head())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isnull().sum())

    print("\nExact duplicate rows:", df.duplicated().sum())


if __name__ == "__main__":
    main()
