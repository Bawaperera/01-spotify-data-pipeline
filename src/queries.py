"""
queries.py
----------
Reusable SQL query functions for Spotify analytics.

Every function:
  1. Opens a connection
  2. Executes a query
  3. Returns a DataFrame
  4. Closes the connection
"""

import sqlite3
import pandas as pd


# ─── Connection helper ───────────────────────────────────────────────────────

def get_connection(db_path: str = "data/processed/spotify.db") -> sqlite3.Connection:
    """Return a SQLite connection to the Spotify database."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=MEMORY")
    conn.execute("PRAGMA synchronous=OFF")
    return conn


# ─── Query functions ─────────────────────────────────────────────────────────

def top_artists_by_popularity(n: int = 10,
                               db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Return top N artists by average track popularity (min 5 tracks)."""
    query = """
    SELECT
        artist_name,
        track_count,
        ROUND(avg_popularity, 2)    AS avg_popularity,
        ROUND(avg_danceability, 3)  AS avg_danceability,
        ROUND(avg_energy, 3)        AS avg_energy,
        total_streams
    FROM artists
    WHERE track_count >= 5
    ORDER BY avg_popularity DESC
    LIMIT ?
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn, params=(n,))
    conn.close()
    return df


def genre_audio_profile(genre: str,
                         db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Return average audio features for a specific genre."""
    query = """
    SELECT
        genre,
        COUNT(*)                        AS track_count,
        ROUND(AVG(popularity), 2)       AS avg_popularity,
        ROUND(AVG(danceability), 3)     AS avg_danceability,
        ROUND(AVG(energy), 3)           AS avg_energy,
        ROUND(AVG(loudness), 2)         AS avg_loudness,
        ROUND(AVG(instrumentalness), 3) AS avg_instrumentalness,
        ROUND(AVG(tempo), 1)            AS avg_tempo,
        ROUND(AVG(duration_min), 2)     AS avg_duration_min
    FROM tracks
    WHERE genre = ?
    GROUP BY genre
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn, params=(genre,))
    conn.close()
    return df


def popularity_distribution(db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Return count and percentage of tracks in each popularity tier."""
    query = """
    SELECT
        popularity_tier,
        COUNT(*) AS track_count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tracks), 2) AS percentage
    FROM tracks
    GROUP BY popularity_tier
    ORDER BY
        CASE popularity_tier
            WHEN 'Low'    THEN 1
            WHEN 'Medium' THEN 2
            WHEN 'High'   THEN 3
        END
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def yearly_trends(db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Return yearly averages for key metrics."""
    query = """
    SELECT
        release_year,
        COUNT(*)                        AS track_count,
        ROUND(AVG(popularity), 2)       AS avg_popularity,
        ROUND(AVG(danceability), 3)     AS avg_danceability,
        ROUND(AVG(energy), 3)           AS avg_energy,
        ROUND(AVG(tempo), 1)            AS avg_tempo,
        ROUND(AVG(duration_min), 2)     AS avg_duration_min,
        ROUND(AVG(instrumentalness), 3) AS avg_instrumentalness
    FROM tracks
    WHERE release_year IS NOT NULL
      AND release_year BETWEEN 2015 AND 2025
    GROUP BY release_year
    ORDER BY release_year
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def top_danceable_tracks(n: int = 20,
                          db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Return most danceable tracks with popularity > 50."""
    query = """
    SELECT
        track_name,
        artist_name,
        genre,
        ROUND(danceability, 3) AS danceability,
        ROUND(energy, 3)       AS energy,
        popularity,
        release_year
    FROM tracks
    WHERE popularity > 50
    ORDER BY danceability DESC
    LIMIT ?
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn, params=(n,))
    conn.close()
    return df


def genre_comparison(db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Compare audio features across all genres (ordered by avg popularity)."""
    query = """
    SELECT
        genre,
        COUNT(*)                        AS track_count,
        ROUND(AVG(popularity), 2)       AS avg_popularity,
        ROUND(AVG(danceability), 3)     AS avg_danceability,
        ROUND(AVG(energy), 3)           AS avg_energy,
        ROUND(AVG(loudness), 2)         AS avg_loudness,
        ROUND(AVG(instrumentalness), 3) AS avg_instrumentalness,
        ROUND(AVG(tempo), 1)            AS avg_tempo,
        ROUND(AVG(duration_min), 2)     AS avg_duration_min
    FROM tracks
    GROUP BY genre
    ORDER BY avg_popularity DESC
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def artist_deep_dive(artist_name: str,
                      db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Return all tracks and stats for a specific artist."""
    query = """
    SELECT
        track_name,
        album_name,
        genre,
        release_year,
        ROUND(duration_min, 2) AS duration_min,
        popularity,
        popularity_tier,
        ROUND(danceability, 3) AS danceability,
        ROUND(energy, 3)       AS energy,
        ROUND(loudness, 2)     AS loudness,
        ROUND(instrumentalness, 3) AS instrumentalness,
        ROUND(tempo, 1)        AS tempo,
        stream_count,
        explicit
    FROM tracks
    WHERE LOWER(artist_name) LIKE LOWER(?)
    ORDER BY popularity DESC
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn, params=(f"%{artist_name}%",))
    conn.close()
    return df


def popularity_by_genre_year(db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Return average popularity per genre per year (for heatmap/trend charts)."""
    query = """
    SELECT
        release_year,
        genre,
        COUNT(*)                  AS track_count,
        ROUND(AVG(popularity), 2) AS avg_popularity
    FROM tracks
    WHERE release_year BETWEEN 2015 AND 2025
    GROUP BY release_year, genre
    ORDER BY release_year, genre
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def duration_vs_popularity(db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Bin tracks by duration range and return average popularity per bin."""
    query = """
    SELECT
        CASE
            WHEN duration_min < 2       THEN '< 2 min'
            WHEN duration_min < 3       THEN '2-3 min'
            WHEN duration_min < 4       THEN '3-4 min'
            WHEN duration_min < 5       THEN '4-5 min'
            WHEN duration_min < 6       THEN '5-6 min'
            ELSE                             '6+ min'
        END AS duration_range,
        COUNT(*) AS track_count,
        ROUND(AVG(popularity), 2) AS avg_popularity
    FROM tracks
    GROUP BY duration_range
    ORDER BY MIN(duration_min)
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def explicit_content_analysis(db_path: str = "data/processed/spotify.db") -> pd.DataFrame:
    """Compare popularity between explicit and non-explicit tracks."""
    query = """
    SELECT
        CASE WHEN explicit = 1 THEN 'Explicit' ELSE 'Clean' END AS content_type,
        COUNT(*) AS track_count,
        ROUND(AVG(popularity), 2)   AS avg_popularity,
        ROUND(AVG(danceability), 3) AS avg_danceability,
        ROUND(AVG(energy), 3)       AS avg_energy
    FROM tracks
    GROUP BY explicit
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
