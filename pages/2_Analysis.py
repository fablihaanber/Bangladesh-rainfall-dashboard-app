import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils import (
    SHARED_CSS, MONTH_SHORT, METRIC_LABELS,
    load_data, render_page_header,
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

df = load_data()

all_districts = sorted(df["district"].unique())
all_years     = sorted(df["year"].unique())

# ── Filters row ───────────────────────────────────────────────────
f1, f2, f3 = st.columns([2, 1.2, 1.2])
with f1:
    selected_districts = st.multiselect(
        "Districts", options=all_districts,
        default=all_districts[:5],
        help="Select one or more districts to compare"
    )
with f2:
    selected_metric = st.selectbox(
        "Metric", options=list(METRIC_LABELS.keys()),
        format_func=lambda x: METRIC_LABELS[x]
    )
with f3:
    selected_years = st.multiselect(
        "Years", options=all_years, default=all_years,
    )

if not selected_districts:
    st.warning("Select at least one district to see charts.")
    st.stop()

mask = (
    df["district"].isin(selected_districts) &
    df["year"].isin(selected_years)
)
dff = df[mask].copy()
dff["month_label"] = dff["month"].map(MONTH_SHORT)

st.markdown("<br>", unsafe_allow_html=True)

# ── Chart 1: Monthly average across selected districts ────────────
st.markdown('<div class="chart-title">Monthly average rainfall — all selected districts</div>', unsafe_allow_html=True)

monthly_avg = (
    dff.groupby("month")[selected_metric]
    .mean()
    .reset_index()
)
monthly_avg["month_label"] = monthly_avg["month"].map(MONTH_SHORT)
monthly_avg = monthly_avg.sort_values("month")

fig1 = px.bar(
    monthly_avg, x="month_label", y=selected_metric,
    labels={"month_label": "Month", selected_metric: METRIC_LABELS[selected_metric]},
    color_discrete_sequence=["#0082ff"],
)
fig1.update_layout(**PLOTLY_LAYOUT)
fig1.update_traces(marker_line_width=0)
st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Year-over-year trend per district ────────────────────
st.markdown('<div class="chart-title">Year-over-year trend by district</div>', unsafe_allow_html=True)

yearly = (
    dff.groupby(["year", "district"])[selected_metric]
    .mean()
    .reset_index()
)

fig2 = px.line(
    yearly, x="year", y=selected_metric, color="district",
    markers=True,
    labels={"year": "Year", selected_metric: METRIC_LABELS[selected_metric], "district": "District"},
    color_discrete_sequence=px.colors.qualitative.Safe,
)
fig2.update_layout(**PLOTLY_LAYOUT)
st.plotly_chart(fig2, use_container_width=True)

# ── Chart 3: Monthly heatmap per district ────────────────────────
if len(selected_districts) <= 10:
    st.markdown('<div class="chart-title">Monthly rainfall heatmap by district</div>', unsafe_allow_html=True)

    pivot = (
        dff.groupby(["district", "month"])[selected_metric]
        .mean()
        .reset_index()
        .pivot(index="district", columns="month", values=selected_metric)
        .rename(columns=MONTH_SHORT)
    )

    fig3 = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale="Blues",
        colorbar=dict(title=METRIC_LABELS[selected_metric], tickfont=dict(color="#cecece")),
    ))
    fig3.update_layout(**PLOTLY_LAYOUT, height=max(250, len(selected_districts) * 40 + 80))
    st.plotly_chart(fig3, use_container_width=True)

# ── Chart 4: District ranking (bar) ──────────────────────────────
st.markdown('<div class="chart-title">District ranking by average rainfall</div>', unsafe_allow_html=True)

ranking = (
    dff.groupby("district")[selected_metric]
    .mean()
    .reset_index()
    .sort_values(selected_metric, ascending=True)
)

fig4 = px.bar(
    ranking, x=selected_metric, y="district",
    orientation="h",
    labels={"district": "", selected_metric: METRIC_LABELS[selected_metric]},
    color=selected_metric,
    color_continuous_scale="Blues",
)
fig4.update_layout(**PLOTLY_LAYOUT, height=max(300, len(selected_districts) * 38 + 80),
                   coloraxis_showscale=False)
fig4.update_traces(marker_line_width=0)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("Source: CHIRPS 2020–2025")