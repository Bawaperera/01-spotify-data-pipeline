"""
app.py — Spotify Music Analytics Dashboard
Multi-page Streamlit app powered by the cleaned Spotify dataset.

Run: streamlit run dashboard/app.py
"""

import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spotify Analytics",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Spotify-ish colour palette ───────────────────────────────────────────────
SPOTIFY_GREEN   = "#1DB954"
SPOTIFY_BLACK   = "#191414"
SPOTIFY_DARK    = "#212121"
ACCENT_ORANGE   = "#f39c12"
ACCENT_RED      = "#e74c3c"

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .main {{ background-color: {SPOTIFY_BLACK}; }}
    h1, h2, h3 {{ color: {SPOTIFY_GREEN}; }}
    .metric-card {{
        background: {SPOTIFY_DARK};
        border-radius: 12px;
        padding: 18px 24px;
        text-align: center;
        border: 1px solid #333;
    }}
    .metric-label {{ font-size: 13px; color: #aaa; margin-bottom: 4px; }}
    .metric-value {{ font-size: 28px; font-weight: 700; color: white; }}
    .stSidebar > div:first-child {{ background-color: {SPOTIFY_DARK}; }}
</style>
""", unsafe_allow_html=True)


# ─── Data loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, '..', 'data', 'processed', 'spotify_cleaned.csv')
    df = pd.read_csv(path, parse_dates=['release_date'])
    df['popularity_tier'] = pd.Categorical(
        df['popularity_tier'], categories=['Low', 'Medium', 'High'], ordered=True
    )
    return df

df = load_data()

AUDIO_FEATURES  = ['danceability', 'energy', 'loudness', 'instrumentalness', 'tempo']
ALL_GENRES      = sorted(df['genre'].unique().tolist())
YEAR_MIN        = int(df['release_year'].min())
YEAR_MAX        = int(df['release_year'].max())
TIER_COLORS     = {'Low': ACCENT_RED, 'Medium': ACCENT_ORANGE, 'High': SPOTIFY_GREEN}
GENRE_PALETTE   = px.colors.qualitative.Set2


# ─── Sidebar navigation ───────────────────────────────────────────────────────
st.sidebar.markdown(f"## Spotify Analytics")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Audio Features Explorer",
     "Trend Analysis", "Artist Deep Dive"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Dataset:** {len(df):,} tracks · {df['genre'].nunique()} genres")
st.sidebar.markdown(f"**Years:** {YEAR_MIN}–{YEAR_MAX}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("Spotify Music Analytics Dashboard")
    st.caption("Exploring 85,000 tracks from 2015–2025")

    # ── KPI cards ─────────────────────────────────────────────────────────────
    top_genre  = df['genre'].value_counts().idxmax()
    top_artist = df.groupby('artist_name')['popularity'].mean().idxmax()

    col1, col2, col3, col4 = st.columns(4)
    kpis = [
        (col1, "Total Tracks",        f"{len(df):,}"),
        (col2, "Avg Popularity",       f"{df['popularity'].mean():.1f} / 100"),
        (col3, "Top Genre",            top_genre),
        (col4, "Most Popular Artist",  top_artist),
    ]
    for col, label, value in kpis:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts row ────────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Top 10 Artists by Avg Popularity")
        top10 = (df.groupby('artist_name')
                   .agg(avg_pop=('popularity', 'mean'), tracks=('track_id', 'count'))
                   .query('tracks >= 5')
                   .nlargest(10, 'avg_pop')
                   .reset_index())
        fig = px.bar(
            top10.sort_values('avg_pop'),
            x='avg_pop', y='artist_name',
            orientation='h', text='avg_pop',
            color='avg_pop',
            color_continuous_scale=[[0, '#333'], [1, SPOTIFY_GREEN]],
            labels={'avg_pop': 'Avg Popularity', 'artist_name': 'Artist'},
        )
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font_color='white', showlegend=False,
            coloraxis_showscale=False, height=380,
            margin=dict(l=0, r=20, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Genre Distribution")
        genre_counts = df['genre'].value_counts().reset_index()
        genre_counts.columns = ['genre', 'count']
        fig2 = px.pie(
            genre_counts, names='genre', values='count',
            color_discrete_sequence=GENRE_PALETTE, hole=0.45
        )
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', font_color='white',
            legend=dict(orientation='v', x=1.01, y=0.5),
            height=380, margin=dict(l=0, r=0, t=10, b=10)
        )
        fig2.update_traces(textfont_size=11)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Popularity tier distribution ──────────────────────────────────────────
    st.subheader("Popularity Score Distribution")
    fig3 = px.histogram(
        df, x='popularity', nbins=50, color='popularity_tier',
        color_discrete_map=TIER_COLORS,
        labels={'popularity': 'Popularity Score', 'count': 'Number of Tracks'},
        category_orders={'popularity_tier': ['Low', 'Medium', 'High']},
        barmode='overlay', opacity=0.75
    )
    fig3.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)',
        font_color='white', legend_title='Tier',
        height=320, margin=dict(l=0, r=0, t=10, b=10)
    )
    st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — AUDIO FEATURES EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Audio Features Explorer":
    st.title("Audio Features Explorer")

    # ── Sidebar filters ───────────────────────────────────────────────────────
    st.sidebar.subheader("Filters")
    sel_genres  = st.sidebar.multiselect("Genres", ALL_GENRES, default=ALL_GENRES[:5])
    year_range  = st.sidebar.slider("Release Year", YEAR_MIN, YEAR_MAX, (2018, 2025))
    pop_range   = st.sidebar.slider("Popularity Range", 0, 100, (0, 100))
    x_feat      = st.sidebar.selectbox("X-axis Feature", AUDIO_FEATURES, index=0)
    y_feat      = st.sidebar.selectbox("Y-axis Feature", AUDIO_FEATURES, index=1)

    filt = df[
        df['genre'].isin(sel_genres if sel_genres else ALL_GENRES) &
        df['release_year'].between(*year_range) &
        df['popularity'].between(*pop_range)
    ]

    st.caption(f"Showing **{len(filt):,}** tracks matching filters")

    # ── Scatter ───────────────────────────────────────────────────────────────
    st.subheader(f"{x_feat.capitalize()} vs {y_feat.capitalize()}")
    sample_size = min(len(filt), 5000)
    scatter_df  = filt.sample(sample_size, random_state=42) if len(filt) > sample_size else filt

    fig = px.scatter(
        scatter_df, x=x_feat, y=y_feat,
        color='genre', opacity=0.55, size_max=6,
        color_discrete_sequence=GENRE_PALETTE,
        hover_data=['track_name', 'artist_name', 'popularity'],
        labels={x_feat: x_feat.capitalize(), y_feat: y_feat.capitalize()},
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.15)',
        font_color='white', height=420,
        margin=dict(l=0, r=0, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        # ── Correlation heatmap ───────────────────────────────────────────────
        st.subheader("Correlation Heatmap (filtered)")
        num_cols = ['popularity', 'danceability', 'energy',
                    'loudness', 'instrumentalness', 'tempo', 'duration_min']
        corr = filt[num_cols].corr().round(2)
        fig_heat = px.imshow(
            corr, text_auto=True, color_continuous_scale='RdYlGn',
            zmin=-1, zmax=1, aspect='auto'
        )
        fig_heat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', font_color='white',
            height=380, margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_b:
        # ── Summary statistics ────────────────────────────────────────────────
        st.subheader("Summary Statistics (filtered)")
        stats = filt[['popularity'] + AUDIO_FEATURES].describe().T.round(3)
        st.dataframe(stats, use_container_width=True, height=380)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Trend Analysis":
    st.title("Trend Analysis")

    year_sel = st.slider("Year Range", YEAR_MIN, YEAR_MAX, (2015, 2025))
    yearly_df = df[df['release_year'].between(*year_sel)]

    col1, col2 = st.columns(2)

    with col1:
        # ── Popularity trend ──────────────────────────────────────────────────
        st.subheader("Popularity Trend Over Years")
        pop_trend = (yearly_df.groupby('release_year')['popularity']
                              .agg(['mean', 'std']).reset_index())
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=pop_trend['release_year'], y=pop_trend['mean'],
            mode='lines+markers', name='Avg Popularity',
            line=dict(color=SPOTIFY_GREEN, width=3),
            marker=dict(size=8)
        ))
        fig_trend.add_trace(go.Scatter(
            x=list(pop_trend['release_year']) + list(pop_trend['release_year'])[::-1],
            y=list(pop_trend['mean'] + pop_trend['std']) +
              list(pop_trend['mean'] - pop_trend['std'])[::-1],
            fill='toself', fillcolor='rgba(29,185,84,0.1)',
            line=dict(color='rgba(255,255,255,0)'), name='±1 Std Dev'
        ))
        fig_trend.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.15)',
            font_color='white', height=360,
            margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        # ── Genre distribution over time ──────────────────────────────────────
        st.subheader("Genre Distribution Over Years")
        top5_genres = df['genre'].value_counts().head(5).index.tolist()
        genre_yr = (yearly_df[yearly_df['genre'].isin(top5_genres)]
                    .groupby(['release_year', 'genre'])
                    .size().reset_index(name='count'))
        fig_area = px.area(
            genre_yr, x='release_year', y='count', color='genre',
            color_discrete_sequence=GENRE_PALETTE,
            labels={'release_year': 'Year', 'count': 'Track Count', 'genre': 'Genre'}
        )
        fig_area.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.15)',
            font_color='white', height=360,
            margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(fig_area, use_container_width=True)

    # ── Audio features by year ────────────────────────────────────────────────
    st.subheader("Average Audio Features by Year")
    feat_year = (yearly_df.groupby('release_year')[AUDIO_FEATURES].mean().reset_index())
    sel_feats = st.multiselect("Select features to plot",
                               AUDIO_FEATURES, default=['danceability', 'energy'])
    if sel_feats:
        fig_yr = go.Figure()
        for i, feat in enumerate(sel_feats):
            fig_yr.add_trace(go.Bar(
                x=feat_year['release_year'], y=feat_year[feat],
                name=feat.capitalize(),
                marker_color=GENRE_PALETTE[i % len(GENRE_PALETTE)]
            ))
        fig_yr.update_layout(
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.15)',
            font_color='white', height=360, legend_title='Feature',
            margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(fig_yr, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ARTIST DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Artist Deep Dive":
    st.title("Artist Deep Dive")

    # ── Search ────────────────────────────────────────────────────────────────
    all_artists = sorted(df['artist_name'].unique().tolist())
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        artist1 = st.selectbox("Artist 1", all_artists, index=0)
    with col_s2:
        artist2 = st.selectbox("Artist 2 (comparison)", ["—"] + all_artists, index=0)

    def artist_card(name: str, col):
        a_df = df[df['artist_name'] == name]
        with col:
            st.subheader(f"{name}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Tracks",        len(a_df))
            m2.metric("Avg Popularity", f"{a_df['popularity'].mean():.1f}")
            m3.metric("Genres",         a_df['genre'].nunique())

            # Radar chart of avg audio features
            feats = ['danceability', 'energy', 'instrumentalness']
            vals  = [a_df[f].mean() for f in feats]
            fig_radar = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]], theta=feats + [feats[0]],
                fill='toself', name=name,
                fillcolor=f'rgba(29,185,84,0.25)',
                line=dict(color=SPOTIFY_GREEN, width=2)
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1]),
                           bgcolor='rgba(0,0,0,0)'),
                paper_bgcolor='rgba(0,0,0,0)', font_color='white',
                showlegend=False, height=310,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            # Track table
            st.markdown("**All Tracks (sorted by popularity)**")
            tbl = a_df[['track_name', 'genre', 'release_year',
                         'popularity', 'danceability', 'energy']].sort_values(
                'popularity', ascending=False
            ).reset_index(drop=True)
            st.dataframe(tbl, use_container_width=True, height=260)

    col1, col2 = st.columns(2)
    artist_card(artist1, col1)
    if artist2 != "—":
        artist_card(artist2, col2)

        # ── Side-by-side comparison bar chart ────────────────────────────────
        st.subheader("Head-to-Head Comparison")
        comp_feats = ['popularity', 'danceability', 'energy',
                      'loudness', 'instrumentalness', 'tempo', 'duration_min']
        a1_means = df[df['artist_name'] == artist1][comp_feats].mean()
        a2_means = df[df['artist_name'] == artist2][comp_feats].mean()

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name=artist1, x=comp_feats, y=a1_means.values,
            marker_color=SPOTIFY_GREEN, opacity=0.85
        ))
        fig_comp.add_trace(go.Bar(
            name=artist2, x=comp_feats, y=a2_means.values,
            marker_color=ACCENT_ORANGE, opacity=0.85
        ))
        fig_comp.update_layout(
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.15)',
            font_color='white', height=380,
            xaxis_tickangle=-20,
            margin=dict(l=0, r=0, t=10, b=10)
        )
        st.plotly_chart(fig_comp, use_container_width=True)


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#666; font-size:12px'>"
    "Built by <b>Bawantha</b> | Data: Kaggle Spotify Dataset (2015–2025) | "
    "Spotify Music Analytics Dashboard"
    "</div>",
    unsafe_allow_html=True
)
