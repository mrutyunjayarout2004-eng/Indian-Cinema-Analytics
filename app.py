
import streamlit as st
import pandas as pd
import plotly.express as px
import re
from pathlib import Path

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="Indian Cinema Analytics",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CINEMATIC THEME ----------------
st.markdown("""

<style>
/* FILM FESTIVAL — BURGUNDY & GOLD */
:root {
    --wine: #4B1024;
    --deep-wine: #210812;
    --gold: #E8BC69;
    --cream: #FFF0D6;
    --muted: #C9B8BE;
}

.stApp {
    background:
        radial-gradient(ellipse at top right, #50182C 0%, transparent 45%),
        linear-gradient(135deg, #16070D, #2A0B17 55%, #16070D);
    color: var(--cream);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #250914, #3B1020 70%, #1B070D);
    border-right: 1px solid #75412F;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
h1, h2, h3 {
    color: var(--gold) !important;
}

p, label, [data-testid="stMarkdownContainer"] {
    color: var(--cream);
}

.kpi {
    background:
        radial-gradient(circle at top right, #5A2434, transparent 65%),
        linear-gradient(135deg, #401322, #210A13);
    border: 1px solid #C49A50;
    border-radius: 15px;
    padding: 20px 16px;
    text-align: center;
    min-height: 125px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.kpi:hover {
    transform: translateY(-3px);
    border-color: #FFE0A0;
}

.kpi-label {
    color: #E5D0C8;
    font-size: 13px;
    letter-spacing: 1.1px;
    text-transform: uppercase;
}

.kpi-value {
    color: #F3CD7E;
    font-size: 30px;
    font-weight: 750;
    margin-top: 9px;
}

.movie-card {
    background: #35101E;
    padding: 14px;
    border-radius: 10px;
    border-left: 3px solid var(--gold);
    margin-bottom: 8px;
}

[data-testid="stExpander"] {
    border: 1px solid #815338;
    border-radius: 12px;
    background: rgba(59, 16, 32, 0.45);
}

[data-testid="stDataFrame"] {
    border: 1px solid #6D4539;
    border-radius: 10px;
    overflow: hidden;
}

div[data-testid="stPlotlyChart"] {
    background: rgba(46, 12, 24, 0.42);
    border: 1px solid rgba(196, 154, 80, 0.25);
    border-radius: 14px;
    padding: 8px;
}

.stButton button, .stDownloadButton button {
    background: #681C35;
    color: #FFF0D6;
    border: 1px solid #C49A50;
    border-radius: 9px;
}

.stButton button:hover, .stDownloadButton button:hover {
    background: #842846;
    border-color: #FFE0A0;
    color: white;
}

hr {
    border-color: rgba(232, 188, 105, 0.35);
}
</style>

""", unsafe_allow_html=True)

GOLD = "#E6B85C"
BG = "#152137"

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "indian_movies_cleaned.csv"
    data = pd.read_csv(file_path)
    data.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
        for c in data.columns
    ]
    return data

try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "CSV file not found. Keep app.py and "
        "indian_movies_cleaned.csv in the same folder."
    )
    st.stop()
except Exception as e:
    st.error(f"Could not load the CSV: {e}")
    st.stop()

# ---------------- FIND COLUMNS ----------------
def find_column(candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None

title_col = find_column(["movie_name", "movie_title", "title", "name", "movie"])
year_col = find_column(["year", "release_year", "release_date"])
genre_col = find_column(["genre", "genres"])
rating_col = find_column(["rating", "imdb_rating", "average_rating"])
votes_col = find_column(["votes", "vote_count", "number_of_votes"])
duration_col = find_column(["duration", "runtime", "runtime_minutes"])
director_col = find_column(["director", "directors"])
actor_cols = [
    c for c in ["actor_1", "actor_2", "actor_3", "actors"]
    if c in df.columns
]

if rating_col is None:
    st.error(f"Rating column not found. Available columns: {list(df.columns)}")
    st.stop()

# ---------------- CLEAN NUMERIC VALUES ----------------
def numeric_series(series):
    cleaned = series.astype(str).str.replace(",", "", regex=False)
    cleaned = cleaned.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False)
    return pd.to_numeric(cleaned, errors="coerce")

if year_col:
    df[year_col] = numeric_series(df[year_col])
    df.loc[~df[year_col].between(1800, 2100), year_col] = pd.NA

df[rating_col] = numeric_series(df[rating_col])
if votes_col:
    df[votes_col] = numeric_series(df[votes_col])
if duration_col:
    df[duration_col] = numeric_series(df[duration_col])

# Exclude invalid ratings from rating calculations
rated = df[df[rating_col].between(0, 10)].copy()

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.markdown("# 🎬 CINEMA LAB")
st.sidebar.caption("Indian Movies • Data Explorer")
st.sidebar.markdown("---")
st.sidebar.subheader("Filter the collection")

filtered = df.copy()


if year_col and df[year_col].notna().any():
    years = sorted(df[year_col].dropna().astype(int).unique())
    selected_years = st.sidebar.slider(
        "Release year",
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(int(min(years)), int(max(years)))
    )

    if selected_years != (int(min(years)), int(max(years))):
        filtered = filtered[
            filtered[year_col].between(*selected_years)
        ]


if genre_col:
    all_genres = sorted({
        genre.strip()
        for value in df[genre_col].dropna().astype(str)
        for genre in value.split(",")
        if genre.strip()
    })
    selected_genres = st.sidebar.multiselect(
        "Genre",
        all_genres,
        default=[]
    )
    if selected_genres:
        pattern = "|".join(re.escape(g) for g in selected_genres)
        filtered = filtered[
            filtered[genre_col].astype(str).str.contains(
                pattern, case=False, na=False, regex=True
            )
        ]

if rating_col and rated[rating_col].notna().any():
    min_rating = st.sidebar.slider(
        "Minimum rating",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.5
    )
    filtered = filtered[
        filtered[rating_col].isna()
        | (filtered[rating_col] >= min_rating)
    ]

if votes_col and df[votes_col].notna().any():
    min_votes = st.sidebar.number_input(
        "Minimum votes",
        min_value=0,
        value=0,
        step=100
    )
    filtered = filtered[
        filtered[votes_col].fillna(0) >= min_votes
    ]


# Keep KPI rating calculations aligned with the active filters.
filtered_rated = filtered[filtered[rating_col].between(0, 10)].copy()

# ---------------- CINEMATIC HEADER ----------------
st.html("""
<div style="
    position: relative;
    overflow: hidden;
    padding: 38px 30px 32px;
    border: 1px solid #B88A46;
    border-radius: 18px;
    background:
        radial-gradient(ellipse at 12% 120%, #8A3B26 0%, transparent 42%),
        radial-gradient(ellipse at 88% 0%, #70243C 0%, transparent 48%),
        linear-gradient(120deg, #17060D, #461025 52%, #1A0710);
    box-shadow: 0 12px 34px rgba(0,0,0,0.3);
    margin-bottom: 22px;
">
    <div style="
        color: #E8BC69;
        font-size: 13px;
        letter-spacing: 4px;
        font-weight: 700;
        margin-bottom: 12px;
    ">✦ THE INDIAN CINEMA COLLECTION ✦</div>

    <h1 style="
        color: #FFE0A0 !important;
        font-size: clamp(30px, 4vw, 48px);
        line-height: 1.15;
        margin: 0 0 12px 0;
        letter-spacing: 1px;
    ">🎬 INDIAN CINEMA ANALYTICS</h1>

    <div style="
        color: #E8A18A;
        font-size: 13px;
        letter-spacing: 3px;
        margin-bottom: 17px;
    ">STORIES &nbsp; • &nbsp; STARS &nbsp; • &nbsp; GENRES &nbsp; • &nbsp; TRENDS</div>

    <p style="
        color: #F8E8D8;
        font-size: 16px;
        margin-bottom: 19px;
    ">Exploring movie ratings, genres, filmmakers and audience engagement</p>

    <span style="
        display: inline-block;
        border: 1px solid #B88A46;
        border-radius: 25px;
        padding: 7px 15px;
        color: #F3CD7E;
        font-size: 12px;
        background: rgba(0,0,0,0.18);
    ">INTERACTIVE DASHBOARD &nbsp; | &nbsp; CLEANED MOVIE DATASET</span>

    <div style="
        position: absolute;
        right: 24px;
        top: 22px;
        font-size: 72px;
        opacity: 0.13;
        pointer-events: none;
    ">🎞️</div>
</div>
""")


k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">MOVIES IN VIEW</div>'
        f'<div class="kpi-value">{len(filtered):,}</div></div>',
        unsafe_allow_html=True
    )

with k2:
    avg_rating = filtered_rated[rating_col].mean()
    rating_text = f"{avg_rating:.2f}/10" if pd.notna(avg_rating) else "N/A"
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">AVERAGE RATING</div>'
        f'<div class="kpi-value">{rating_text}</div></div>',
        unsafe_allow_html=True
    )

with k3:
    avg_duration = (
        filtered[duration_col].mean()
        if duration_col else float("nan")
    )
    duration_text = (
        f"{avg_duration:.0f} min"
        if pd.notna(avg_duration) else "N/A"
    )
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">AVERAGE DURATION</div>'
        f'<div class="kpi-value">{duration_text}</div></div>',
        unsafe_allow_html=True
    )

with k4:
    high_rated_count = (
        (filtered[rating_col] >= 8)
        & (filtered[votes_col] >= 1000)
    ).sum() if votes_col else (filtered[rating_col] >= 8).sum()

    st.markdown(
        f'<div class="kpi"><div class="kpi-label">HIGH-RATED MOVIES'
        f'</div><div class="kpi-value">{high_rated_count:,}</div></div>',
        unsafe_allow_html=True
    )

st.markdown("")

# ---------------- PROJECT OVERVIEW ----------------
st.markdown("## 🎞️ Project Overview")

overview_col1, overview_col2, overview_col3 = st.columns(3)

overview_card_style = """
<div style="
    background: linear-gradient(135deg, #401322, #210A13);
    border: 1px solid #B9924B;
    border-radius: 13px;
    padding: 18px 18px 16px;
    min-height: 175px;
">
"""
with overview_col1:
    st.markdown(
        overview_card_style
        + '<div style="color:#E8BC69;font-size:16px;font-weight:700;margin-bottom:10px;">🎯 Objective</div>'
        + '<div style="color:#FFF0D6;line-height:1.7;">Explore Indian movie ratings, release patterns, genres, filmmakers and audience engagement using an interactive data dashboard.</div></div>',
        unsafe_allow_html=True,
    )

with overview_col2:
    st.markdown(
        overview_card_style
        + '<div style="color:#E8BC69;font-size:16px;font-weight:700;margin-bottom:10px;">🗂️ Dataset & Method</div>'
        + f'<div style="color:#FFF0D6;line-height:1.7;">The cleaned CSV currently contains <b>{len(df):,}</b> movie records. The dashboard applies year, genre, rating and vote filters, then summarizes the selected records with charts and tables.</div></div>',
        unsafe_allow_html=True,
    )

with overview_col3:
    st.markdown(
        overview_card_style
        + '<div style="color:#E8BC69;font-size:16px;font-weight:700;margin-bottom:10px;">⚠️ Scope & Limitations</div>'
        + '<div style="color:#FFF0D6;line-height:1.7;">Results depend on the available dataset and missing values. Ratings and votes are not measures of box-office revenue, and correlations do not prove causation.</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------- CHART HELPERS ----------------

def style_chart(fig, height=400):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(25,5,13,0.28)",
        font=dict(
            color="#FFF0D6",
            family="Arial, sans-serif",
            size=12
        ),
        title_font=dict(color="#E8BC69", size=18),
        height=height,
        margin=dict(l=15, r=15, t=60, b=25),
        legend_title_text="",
        colorway=["#E8BC69", "#B85C50", "#D9A15F", "#8B4960"]
    )
    fig.update_xaxes(
        gridcolor="rgba(232,188,105,0.13)",
        zerolinecolor="rgba(232,188,105,0.2)"
    )
    fig.update_yaxes(
        gridcolor="rgba(232,188,105,0.13)",
        zerolinecolor="rgba(232,188,105,0.2)"
    )
    return fig

# ---------------- YEAR ANALYSIS ----------------
st.markdown("## 📈 Release Trends")

if year_col and df[year_col].notna().any():
    left, right = st.columns(2)

    with left:
        yearly_count = (
            filtered.dropna(subset=[year_col])
            .groupby(year_col)
            .size()
            .reset_index(name="Movies")
        )
        fig = px.line(
            yearly_count,
            x=year_col,
            y="Movies",
            markers=True,
            title="Movies Released by Year"
        )
        fig.update_traces(line_color=GOLD, marker_color=GOLD)
        st.plotly_chart(style_chart(fig), width="stretch")

    with right:
        yearly_rating = (
            filtered.dropna(subset=[year_col, rating_col])
            .groupby(year_col)[rating_col]
            .agg(["mean", "count"])
            .reset_index()
        )
        yearly_rating = yearly_rating[yearly_rating["count"] >= 10]
        fig = px.line(
            yearly_rating,
            x=year_col,
            y="mean",
            markers=True,
            title="Average Rating by Year",
            labels={"mean": "Average rating", year_col: "Year"}
        )
        fig.update_traces(line_color=GOLD, marker_color=GOLD)
        st.plotly_chart(style_chart(fig), width="stretch")
else:
    st.info("Year analysis is unavailable because no year column was found.")

# ---------------- GENRE ANALYSIS ----------------
st.markdown("## 🎭 Genre Intelligence")

if genre_col:
    genre_rows = filtered.dropna(subset=[genre_col]).copy()
    genre_rows[genre_col] = genre_rows[genre_col].astype(str).str.split(",")
    genre_rows = genre_rows.explode(genre_col)
    genre_rows[genre_col] = genre_rows[genre_col].str.strip()
    genre_rows = genre_rows[genre_rows[genre_col] != ""]

    left, right = st.columns(2)

    with left:
        genre_counts = (
            genre_rows.groupby(genre_col)
            .size()
            .reset_index(name="Movies")
            .sort_values("Movies", ascending=False)
            .head(12)
        )
        fig = px.bar(
            genre_counts.sort_values("Movies"),
            x="Movies",
            y=genre_col,
            orientation="h",
            title="Most Common Genres",
            color="Movies",
            color_continuous_scale=["#69512C", GOLD]
        )
        st.plotly_chart(style_chart(fig), width="stretch")

    with right:
        genre_ratings = (
            genre_rows.dropna(subset=[rating_col])
            .groupby(genre_col)[rating_col]
            .agg(["mean", "count"])
            .reset_index()
        )
        genre_ratings = genre_ratings[genre_ratings["count"] >= 100]
        genre_ratings = genre_ratings.sort_values("mean", ascending=False).head(12)

        fig = px.bar(
            genre_ratings.sort_values("mean"),
            x="mean",
            y=genre_col,
            orientation="h",
            title="Highest Average Genre Ratings (100+ rated records)",
            labels={"mean": "Average rating"},
            color="mean",
            color_continuous_scale=["#69512C", GOLD]
        )
        st.plotly_chart(style_chart(fig), width="stretch")
else:
    st.info("Genre analysis is unavailable because no genre column was found.")

# ---------------- RATING AND VOTES ----------------
st.markdown("## ⭐ Audience Engagement")

if votes_col:
    engagement = filtered.dropna(subset=[rating_col, votes_col])
    engagement = engagement[engagement[votes_col] > 0]

    if not engagement.empty:
        fig = px.scatter(
            engagement,
            x=votes_col,
            y=rating_col,
            hover_name=title_col if title_col else None,
            title="Movie Rating vs Number of Votes",
            labels={
                votes_col: "Number of votes",
                rating_col: "Rating"
            },
            opacity=0.6
        )
        fig.update_traces(marker_color=GOLD, marker_size=7)
        fig.update_xaxes(type="log")
        st.plotly_chart(style_chart(fig, 450), width="stretch")

        corr = engagement[[rating_col, votes_col]].corr().iloc[0, 1]
        st.caption(
            f"Pearson correlation in the current filtered data: {corr:.3f}. "
            "Correlation does not imply causation."
        )

# ---------------- DIRECTORS AND ACTORS ----------------
st.markdown("## 🎥 People Behind the Movies")

left, right = st.columns(2)

with left:
    if director_col:
        directors = filtered.dropna(subset=[director_col, rating_col])
        director_stats = (
            directors.groupby(director_col)[rating_col]
            .agg(["mean", "count"])
            .reset_index()
        )
        director_stats = director_stats[director_stats["count"] >= 5]
        director_stats = director_stats.sort_values(
            ["mean", "count"], ascending=False
        ).head(10)

        if not director_stats.empty:
            fig = px.bar(
                director_stats.sort_values("mean"),
                x="mean",
                y=director_col,
                orientation="h",
                title="Top Directors by Average Rating (5+ movies)",
                labels={"mean": "Average rating"},
                color="mean",
                color_continuous_scale=["#69512C", GOLD]
            )
            st.plotly_chart(style_chart(fig), width="stretch")
        else:
            st.info("Not enough director records for this selection.")

with right:
    if actor_cols:
        actor_frames = []
        for col in actor_cols:
            part = filtered[[col, rating_col]].dropna().copy()
            part.columns = ["Actor", "Rating"]
            actor_frames.append(part)

        actors = pd.concat(actor_frames, ignore_index=True)
        actors["Actor"] = actors["Actor"].astype(str).str.strip()
        actors = actors[actors["Actor"] != ""]

        actor_stats = (
            actors.groupby("Actor")["Rating"]
            .agg(["mean", "count"])
            .reset_index()
        )
        actor_stats = actor_stats[actor_stats["count"] >= 5]
        actor_stats = actor_stats.sort_values(
            ["mean", "count"], ascending=False
        ).head(10)

        if not actor_stats.empty:
            fig = px.bar(
                actor_stats.sort_values("mean"),
                x="mean",
                y="Actor",
                orientation="h",
                title="Top Actors by Average Rating (5+ appearances)",
                labels={"mean": "Average rating"},
                color="mean",
                color_continuous_scale=["#69512C", GOLD]
            )
            st.plotly_chart(style_chart(fig), width="stretch")
        else:
            st.info("Not enough actor records for this selection.")
    else:
        st.info("Actor analysis is unavailable because actor columns were not found.")

# ---------------- KEY FINDINGS ----------------
st.markdown("## 💡 Key Findings")

st.html("""
<div style="
    background: linear-gradient(135deg, #401322, #210A13);
    border: 1px solid #B9924B;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
">
    <h3 style="color: #E8BC69;">What the data tells us</h3>
    <ul style="line-height: 2; color: #F4F0E8;">
        <li><b>Genre preference:</b> Drama is the most frequently represented
        genre in the dataset.</li>
        <li><b>Audience engagement:</b> The full-dataset correlation between
        ratings and votes is approximately 0.127, indicating a weak positive
        linear relationship.</li>
        <li><b>People behind the films:</b> Director and actor rankings use
        a minimum of five rated movies or appearances to reduce the influence
        of very small samples.</li>
        <li><b>Popular, highly rated films:</b> The dashboard identifies movies
        rated 8 or above with at least 1,000 votes.</li>
        <li><b>Interpretation:</b> These results describe the available dataset
        and do not establish causation or measure box-office performance.</li>
    </ul>
</div>
""")

# ---------------- TOP MOVIES TABLE ----------------
st.markdown("## 🏆 Popular, Highly Rated Movies")

if title_col and votes_col:
    top_movies = filtered[
        (filtered[rating_col] >= 8)
        & (filtered[votes_col] >= 1000)
    ].sort_values(votes_col, ascending=False)

    display_cols = [title_col, rating_col, votes_col]
    if year_col:
        display_cols.insert(1, year_col)
    if genre_col:
        display_cols.append(genre_col)
    if director_col:
        display_cols.append(director_col)

    if not top_movies.empty:
        st.dataframe(
            top_movies[display_cols].head(25),
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No movies match these high-rating and vote filters.")
else:
    st.info("Movie titles or vote counts were not found.")

# ---------------- DATA PREVIEW AND DOWNLOAD ----------------
with st.expander("🔎 Explore filtered data"):
    st.write(f"Showing {len(filtered):,} movie records.")
    st.dataframe(filtered.head(100), width="stretch")
    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="indian_movies_filtered.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption(
    "Indian Cinema Analytics | Educational data project. "
    "Ratings and votes reflect the available dataset, not financial performance."
)
