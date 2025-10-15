import pandas as pd

DATASET_PATH = "data/final_dataset.csv"  # Adjust to your dataset path

def inspect_and_fix_dataset(csv_path):
    df = pd.read_csv(csv_path)

    errors = []

    # Check required columns exist
    required_cols = ["title", "genre", "description", "type", "rating", "year"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # Check empty titles
    if df["title"].isnull().any() or (df["title"].astype(str).str.strip() == "").any():
        errors.append("Some titles are missing or empty")

    # Check 'type' values
    allowed_types = {"movie", "anime", "series"}
    invalid_types = set(df["type"].dropna().str.lower().unique()) - allowed_types
    if invalid_types:
        errors.append(f"Invalid 'type' values found: {invalid_types}")

    if not df["type"].dropna().apply(lambda x: x.islower()).all():
        errors.append("Not all 'type' values are lowercase strings")

    # Check 'rating' numeric range
    if df["rating"].isnull().any():
        errors.append("Some rating values are null")
    elif ((df["rating"] < 0) | (df["rating"] > 10)).any():
        errors.append("Rating values must be between 0 and 10")

    # Convert year to numeric for checks and fixing
    df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Check invalid years: allow 0 as valid fallback
    invalid_years = df[(df["year"].isnull()) | (df["year"] < 0) | (df["year"] > 2100)]
    if not invalid_years.empty:
        errors.append(f"{len(invalid_years)} rows have invalid or missing 'year' values")

    # Check duplicate titles ignoring case and whitespace
    normalized_titles = df["title"].astype(str).str.strip().str.lower()
    dup_titles = normalized_titles[normalized_titles.duplicated()]
    if not dup_titles.empty:
        errors.append(f"Duplicate titles found (case-insensitive): {dup_titles.unique()}")

    # Check description completeness
    if df["description"].isnull().any() or (df["description"].astype(str).str.strip() == "").any():
        errors.append("Some description fields are missing or empty")

    # Print current errors
    if len(errors) == 0:
        print("✅ Dataset passed all inspection checks!")
    else:
        print("❌ Dataset inspection issues:")
        for e in errors:
            print(f" - {e}")

    # Auto-fix invalid years by setting them to 0
    if not invalid_years.empty:
        print(f"Fixing {len(invalid_years)} invalid/missing year entries by setting to 0...")
        df.loc[(df["year"].isnull()) | (df["year"] < 0) | (df["year"] > 2100), "year"] = 0
        df["year"] = df["year"].astype(int)

        # Save fixed dataset overwrite
        df.to_csv(csv_path, index=False)
        print(f"Dataset saved after fixing year values to '{csv_path}'")

        # Re-check invalid years (allowing 0)
        invalid_years_after = df[(df["year"] < 0) | (df["year"] > 2100)]

        if invalid_years_after.empty:
            print("✅ All 'year' values are now valid after fix.")
        else:
            print(f"❌ {len(invalid_years_after)} 'year' values remain invalid after fix.")

    return df

if __name__ == "__main__":
    inspect_and_fix_dataset(DATASET_PATH)
