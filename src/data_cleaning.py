"""
data_cleaning.py
----------------
Reusable cleaning functions for the Spotify 2015-2025 dataset.
Dataset columns:
  track_id, track_name, artist_name, album_name, release_date, genre,
  duration_ms, popularity, danceability, energy, key, loudness, mode,
  instrumentalness, tempo, stream_count, country, explicit, label
"""

import pandas as pd
import numpy as np


# ─── 1. Load ────────────────────────────────────────────────────────────────

def load_raw_data(filepath: str) -> pd.DataFrame:
    """Load raw CSV and return a DataFrame."""
    df = pd.read_csv(filepath)
    print(f" Loaded {len(df):,} rows × {df.shape[1]} columns from '{filepath}'")
    return df


# ─── 2. Normalize column names ───────────────────────────────────────────────

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all column names to lowercase snake_case."""
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    print(f" Column names normalised: {df.columns.tolist()}")
    return df


# ─── 3. Remove duplicates ────────────────────────────────────────────────────

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows and print how many were dropped."""
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    print(f" Removed {removed:,} duplicate rows — {len(df):,} remain")
    return df


# ─── 4. Handle missing values ────────────────────────────────────────────────

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strategy:
    - Numerical columns  → fill with median
    - Categorical columns → fill with 'Unknown'
    - Drop rows where >50 % of columns are null
    """
    df = df.copy()

    # Drop rows that are mostly empty first
    threshold = df.shape[1] * 0.5
    before = len(df)
    df = df.dropna(thresh=int(threshold))
    print(f"  Dropped {before - len(df):,} rows with >50 % nulls")

    # Numerical → median fill
    num_cols = df.select_dtypes(include="number").columns
    for col in num_cols:
        n = df[col].isnull().sum()
        if n > 0:
            df[col] = df[col].fillna(df[col].median())
            print(f"  '{col}': filled {n} nulls with median ({df[col].median():.2f})")

    # Categorical → 'Unknown'
    cat_cols = df.select_dtypes(include="object").columns
    for col in cat_cols:
        n = df[col].isnull().sum()
        if n > 0:
            df[col] = df[col].fillna("Unknown")
            print(f"  '{col}': filled {n} nulls with 'Unknown'")

    print(f" Missing-value handling complete — {df.isnull().sum().sum()} nulls remaining")
    return df


# ─── 5. Fix data types ───────────────────────────────────────────────────────

def fix_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    - Convert release_date → datetime
    - Convert genre, country, label, mode, key → category dtype
    - Ensure explicit is boolean
    """
    df = df.copy()

    # Dates
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    # Categories
    for col in ["genre", "country", "label"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # mode / key are integers but semantically categorical
    for col in ["mode", "key"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # explicit → bool
    if "explicit" in df.columns:
        df["explicit"] = df["explicit"].astype(bool)

    print(" Data types fixed")
    print(df.dtypes.to_string())
    return df


# ─── 6. Remove outliers ──────────────────────────────────────────────────────

def remove_outliers(df: pd.DataFrame,
                    columns: list,
                    method: str = "iqr") -> pd.DataFrame:
    """
    Remove outliers from numerical columns.
    method='iqr' uses the 1.5×IQR rule.
    """
    df = df.copy()
    before = len(df)

    for col in columns:
        if col not in df.columns:
            continue
        if method == "iqr":
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = df[col].between(lower, upper)
            removed = (~mask).sum()
            df = df[mask]
            print(f"  '{col}': removed {removed:,} outliers (IQR [{lower:.2f}, {upper:.2f}])")

    print(f" Outlier removal: {before - len(df):,} rows removed — {len(df):,} remain")
    return df


# ─── 7. Feature engineering ──────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create new columns:
    - release_year   : int year extracted from release_date
    - release_month  : int month extracted from release_date
    - duration_min   : duration in minutes (duration_ms / 60000)
    - popularity_tier: 'Low' (0-33), 'Medium' (34-66), 'High' (67-100)
    - energy_level   : 'Low' / 'Medium' / 'High' based on energy column
    - is_danceable   : True if danceability > 0.6
    - stream_millions: stream_count expressed in millions (rounded 2dp)
    """
    df = df.copy()

    # Temporal
    df["release_year"]  = df["release_date"].dt.year.astype("Int64")
    df["release_month"] = df["release_date"].dt.month.astype("Int64")

    # Duration
    df["duration_min"] = (df["duration_ms"] / 60_000).round(2)

    # Popularity tier
    df["popularity_tier"] = pd.cut(
        df["popularity"],
        bins=[-1, 33, 66, 100],
        labels=["Low", "Medium", "High"]
    )

    # Energy level
    df["energy_level"] = pd.cut(
        df["energy"],
        bins=[-0.01, 0.33, 0.66, 1.0],
        labels=["Low", "Medium", "High"]
    )

    # Danceability flag
    df["is_danceable"] = df["danceability"] > 0.6

    # Streams in millions
    df["stream_millions"] = (df["stream_count"] / 1_000_000).round(2)

    print(f" Feature engineering complete — added 7 new columns")
    print(f"   New columns: release_year, release_month, duration_min, "
          f"popularity_tier, energy_level, is_danceable, stream_millions")
    return df


# ─── 8. Full pipeline ────────────────────────────────────────────────────────

def clean_pipeline(filepath: str) -> pd.DataFrame:
    """Run all cleaning steps in order and return the cleaned DataFrame."""
    print("\n" + "="*55)
    print("  SPOTIFY DATA CLEANING PIPELINE")
    print("="*55)

    df = load_raw_data(filepath)
    df = normalize_column_names(df)
    df = remove_duplicates(df)
    df = handle_missing_values(df)
    df = fix_data_types(df)
    df = engineer_features(df)

    print("\n" + "="*55)
    print(f"   Pipeline complete — final shape: {df.shape}")
    print("="*55 + "\n")
    return df
