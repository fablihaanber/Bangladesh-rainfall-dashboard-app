import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import (
    SHARED_CSS, MONTH_SHORT, METRIC_LABELS,
    load_dataset, render_page_header,
)

st.set_page_config(
    page_title="Analysis — BD Raindrop",
    # page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Extra chart styling for dark theme
st.markdown("""
<style>
.chart-title {
    color: #e6e6e6;
    font-size: 15px;
    font-weight: 600;
    margin: 18px 0 6px 0;
}
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#1a1a1a",
    font_color="#cecece",
    font_size=12,
    margin=dict(t=30, b=30, l=10, r=10),
    xaxis=dict(gridcolor="#2e2e2e", linecolor="#3a3a3a"),
    yaxis=dict(gridcolor="#2e2e2e", linecolor="#3a3a3a"),
)

render_page_header("Analysis")

df = load_dataset()

all_districts = sorted(df["district"].unique())
all_years     = sorted(df["year"].unique())

# Season classification
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.strftime("%B")

pre_monsoon_months  = ["March", "April", "May"]
monsoon_months      = ["June", "July", "August", "September"]
post_monsoon_months = ["October", "November"]
winter_months       = ["December", "January", "February"]

def classify_seasonal_rainfall(month):
    if month in pre_monsoon_months:
        return "pre_monsoon"
    elif month in monsoon_months:
        return "monsoon"
    elif month in post_monsoon_months:
        return "post_monsoon"
    else:
        return "winter"

df["rainfall_season"] = df["month"].apply(classify_seasonal_rainfall)

# ── Filter ────────────────────────────────────────────────────────
selected_season = st.selectbox(
    "Season",
    options=["pre_monsoon", "monsoon", "post_monsoon", "winter"],
    format_func=lambda x: x.replace("_", " ").title()
)

dff = df[df["rainfall_season"] == selected_season]

# ── Aggregations ──────────────────────────────────────────────────
annual_mean_rainfall = (
    dff.groupby(["year", "district"])["total_rainfall"].sum().reset_index()
    .groupby("year")["total_rainfall"].mean().reset_index()
)

annual_max = dff.groupby("year")["max_rainfall"].mean().reset_index()
annual_min = dff.groupby("year")["min_rainfall"].mean().reset_index()
annual_max["type"] = "Max Rainfall"
annual_min["type"] = "Min Rainfall"
annual_min = annual_min.rename(columns={"min_rainfall": "max_rainfall"})
combined = pd.concat([annual_max, annual_min])

# ── Chart 1: Annual Mean Rainfall ─────────────────────────────────
st.markdown('<div class="chart-title">Annual Mean Rainfall (mm)</div>', unsafe_allow_html=True)

fig1 = px.bar(
    annual_mean_rainfall, x="year", y="total_rainfall",
    labels={"year": "Year", "total_rainfall": "Mean Rainfall Totals (mm)"},
    color_discrete_sequence=["#0082ff"],
)
fig1.update_layout(**PLOTLY_LAYOUT)
fig1.update_layout(
    height=400,
    yaxis=dict(range=[0, annual_mean_rainfall["total_rainfall"].max() * 1.5])
)
fig1.update_traces(marker_line_width=0)
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Max vs Min Rainfall ──────────────────────────────────
st.markdown('<div class="chart-title">Max vs Min Rainfall (mm)</div>', unsafe_allow_html=True)

fig2 = px.line(
    combined, x="year", y="max_rainfall", color="type",
    markers=True,
    labels={"year": "Year", "max_rainfall": "Rainfall (mm)", "type": "Type"},
    color_discrete_sequence=["#0082ff", "#ff6b6b"],
)
fig2.update_layout(**PLOTLY_LAYOUT)
fig2.update_layout(
    height=400,
    yaxis=dict(range=[0, combined["max_rainfall"].max() * 2])
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Source: CHIRPS 2020–2025")