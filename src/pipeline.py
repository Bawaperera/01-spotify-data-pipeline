"""
pipeline.py
-----------
ETL pipeline: Raw CSV → Clean → SQLite Database

Usage:
    python src/pipeline.py
"""

import sqlite3
import os
import sys
import pandas as pd

# Allow running from project root
sys.path.insert(0, os.path.dirname(__file__))
from data_cleaning import clean_pipeline


# ─── Schema ─────────────────────────────────────────────────────────────────

CREATE_TRACKS_TABLE = """
CREATE TABLE IF NOT EXISTS tracks (
    track_id         TEXT PRIMARY KEY,
    track_name       TEXT,
    artist_name      TEXT,
    album_name       TEXT,
    release_date     TEXT,
    release_year     INTEGER,
    release_month    INTEGER,
    genre            TEXT,
    duration_ms      INTEGER,
    duration_min     REAL,
    popularity       INTEGER,
    popularity_tier  TEXT,
    danceability     REAL,
    is_danceable     INTEGER,
    energy           REAL,
    energy_level     TEXT,
    key              INTEGER,
    loudness         REAL,
    mode             INTEGER,
    instrumentalness REAL,
    tempo            REAL,
    stream_count     INTEGER,
    stream_millions  REAL,
    country          TEXT,
    explicit         INTEGER,
    label            TEXT
);
"""

CREATE_ARTISTS_TABLE = """
CREATE TABLE IF NOT EXISTS artists (
    artist_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    artist_name    TEXT UNIQUE,
    track_count    INTEGER,
    avg_popularity REAL,
    avg_danceability REAL,
    avg_energy     REAL,
    total_streams  INTEGER
);
"""

CREATE_GENRES_TABLE = """
CREATE TABLE IF NOT EXISTS genres (
    genre_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    genre          TEXT UNIQUE,
    track_count    INTEGER,
    avg_popularity REAL,
    avg_danceability REAL,
    avg_energy     REAL,
    avg_tempo      REAL
);
"""


# ─── Create DB ───────────────────────────────────────────────────────────────

def create_database(db_path: str = "data/processed/spotify.db") -> sqlite3.Connection:
    """Create SQLite database with schema tables."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=MEMORY")
    conn.execute("PRAGMA synchronous=OFF")
    cur = conn.cursor()
    cur.execute(CREATE_TRACKS_TABLE)
    cur.execute(CREATE_ARTISTS_TABLE)
    cur.execute(CREATE_GENRES_TABLE)
    conn.commit()
    print(f" Database created at '{db_path}'")
    return conn


# ─── Load data ───────────────────────────────────────────────────────────────

def load_to_database(df: pd.DataFrame,
                     conn: sqlite3.Connection) -> None:
    """Load cleaned DataFrame into SQLite tables."""

    # ── tracks table ──────────────────────────────────────────────────────
    tracks_cols = [
        "track_id", "track_name", "artist_name", "album_name",
        "release_date", "release_year", "release_month", "genre",
        "duration_ms", "duration_min", "popularity", "popularity_tier",
        "danceability", "is_danceable", "energy", "energy_level",
        "key", "loudness", "mode", "instrumentalness", "tempo",
        "stream_count", "stream_millions", "country", "explicit", "label"
    ]
    tracks_df = df[[c for c in tracks_cols if c in df.columns]].copy()
    tracks_df["release_date"] = tracks_df["release_date"].astype(str)
    tracks_df["is_danceable"] = tracks_df["is_danceable"].astype(int)
    tracks_df["explicit"] = tracks_df["explicit"].astype(int)

    # Convert categoricals to strings for SQLite
    for col in ["genre", "country", "label", "popularity_tier", "energy_level"]:
        if col in tracks_df.columns:
            tracks_df[col] = tracks_df[col].astype(str)

    tracks_df.to_sql("tracks", conn, if_exists="replace", index=False)
    print(f"   tracks table: {len(tracks_df):,} rows loaded")

    # ── artists aggregate table ───────────────────────────────────────────
    artists_df = (
        df.groupby("artist_name", as_index=False)
        .agg(
            track_count    =("track_id", "count"),
            avg_popularity =("popularity", "mean"),
            avg_danceability=("danceability", "mean"),
            avg_energy     =("energy", "mean"),
            total_streams  =("stream_count", "sum"),
        )
    )
    artists_df["avg_popularity"]   = artists_df["avg_popularity"].round(2)
    artists_df["avg_danceability"] = artists_df["avg_danceability"].round(3)
    artists_df["avg_energy"]       = artists_df["avg_energy"].round(3)
    artists_df.to_sql("artists", conn, if_exists="replace", index=False)
    print(f"   artists table: {len(artists_df):,} artists loaded")

    # ── genres aggregate table ────────────────────────────────────────────
    genres_df = (
        df.groupby("genre", as_index=False)
        .agg(
            track_count    =("track_id", "count"),
            avg_popularity =("popularity", "mean"),
            avg_danceability=("danceability", "mean"),
            avg_energy     =("energy", "mean"),
            avg_tempo      =("tempo", "mean"),
        )
    )
    for col in ["avg_popularity", "avg_danceability", "avg_energy", "avg_tempo"]:
        genres_df[col] = genres_df[col].round(2)
    genres_df.to_sql("genres", conn, if_exists="replace", index=False)
    print(f"   genres table: {len(genres_df):,} genres loaded")

    conn.commit()


# ─── Full pipeline ───────────────────────────────────────────────────────────

def run_pipeline(raw_path: str,
                 db_path:  str = "data/processed/spotify.db") -> None:
    """Run complete ETL: CSV → clean → SQLite."""
    print("\n" + "="*55)
    print("  SPOTIFY ETL PIPELINE")
    print("="*55)

    # Step 1: Clean
    print("\n[1/3] Cleaning data …")
    df = clean_pipeline(raw_path)

    # Step 2: Save cleaned CSV
    cleaned_path = "data/processed/spotify_cleaned.csv"
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(cleaned_path, index=False)
    print(f"\n[2/3] Cleaned CSV saved → '{cleaned_path}'")

    # Step 3: Load to SQLite
    # Build in /tmp first to avoid journal-file issues on mounted filesystems,
    # then copy the finished database to the target path.
    import tempfile, shutil
    tmp_db = os.path.join(tempfile.gettempdir(), 'spotify_tmp.db')
    print(f"\n[3/3] Building SQLite DB in temp location …")
    conn = create_database(tmp_db)
    load_to_database(df, conn)
    conn.close()

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    shutil.copy2(tmp_db, db_path)
    os.remove(tmp_db)
    print(f"      Copied to '{db_path}'")

    print("\n" + "="*55)
    print("   ETL COMPLETE")
    print(f"  Rows processed : {len(df):,}")
    print(f"  Cleaned CSV    : {cleaned_path}")
    print(f"  SQLite DB      : {db_path}")
    print("="*55 + "\n")


if __name__ == "__main__":
    # Run from the project root: python src/pipeline.py
    raw = "data/raw/spotify_2015_2025_85k.csv"
    run_pipeline(raw)
