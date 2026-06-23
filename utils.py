import json
import pandas as pd
import geopandas as gpd
import streamlit as st

MONTH_SHORT = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
}
METRIC_LABELS = {
    "mean_rainfall":  "Mean (mm)",
    "total_rainfall": "Total (mm)",
    "max_rainfall":   "Max (mm)",
}
RAINFALL_CATEGORIES = {
    "No precipitation":     (0, 0),
    "Very light (0-2.5mm)": (0, 2.5),
    "Light (2.5-7.5mm)":    (2.5, 7.5),
    "Moderate (7.5-35mm)":  (7.5, 35),
    "Heavy (35-65mm)":      (35, 65),
    "Very heavy (65mm+)":   (65, float("inf")),
}

def load_map_css():
    with open("styles.css", "r") as f:
        return f"<style>{f.read()}</style>"
    
SHARED_CSS = """
<style>
    .stApp { background-color: #141414; }
    [data-testid="stSidebar"] {
        background-color: #0d0d0d;
        border-right: 1px solid #2a2a2a;
        width: 100px !important; 
    }
    [data-testid="stHeader"] { background-color: #0d0d0d; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }

    /* Sidebar nav links */
    [data-testid="stSidebarNav"] a {
        color: #cecece !important;
        font-weight: 500;
        border-radius: 6px;
        padding: 6px 12px;
    }
    [data-testid="stSidebarNav"] a:hover {
        background-color: #1a1a1a;
        color: #0082ff !important;
    }
    [data-testid="stSidebarNav"] [aria-selected="true"] {
        background-color: #0082ff !important;
        color: white !important;
    }

    /* Date input inline label */
    [data-testid="stDateInput"] {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    [data-testid="stDateInput"] label {
        white-space: nowrap;
        min-width: fit-content;
        margin-bottom: 0 !important;
    }
    [data-testid="stDateInput"] > div {
        flex: 1;
    }

    /* Page header */
    .page-header {
        background-color: #0d0d0d;
        border: 1px solid #262626;
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .page-header-title {
        font-size: 24px;
        font-weight: 700;
        margin: 0;
        line-height: 38px;
    }
    .page-header-title .brand { color: #0379a8; }
    .page-header-title .sub   { color: #cecece; }
    .page-header-badge {
        background-color: #0082ff;
        color: white;
        font-size: 12px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        margin-left: 4px;
    }

    /* KPI cards */
    .kpi-box {
        background-color: #1e1e1e;
        border: 1px solid #2e2e2e;
        border-radius: 12px;
        padding: 16px 18px;
        text-align: left;
    }
    .kpi-label {
        color: #aaaaaa;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 6px;
    }
    .kpi-value {
        color: #f5f5f5;
        font-size: 24px;
        font-weight: 700;
    }

    /* Filter section */
    .filter-heading {
        color: #cecece;
        font-size: 15px;
        font-weight: 600;
        margin-top: 14px;
        margin-bottom: 2px;
    }
    .filter-underline {
        border: none;
        border-top: 1px solid #3a3a3a;
        margin-top: 4px;
        margin-bottom: 10px;
    }
    div[role="radiogroup"] {
        flex-direction: row !important;
        flex-wrap: wrap;
        gap: 6px;
    }
    div[role="radiogroup"] label {
        background-color: #1f1f1f;
        border: 1px solid #3a3a3a;
        border-radius: 6px;
        padding: 5px 8px;
        margin: 0 !important;
        color: #cecece !important;
        font-size: 12.5px;
        cursor: pointer;
        flex: 0 0 auto;
        min-width: 56px;
        text-align: center;
    }
    div[role="radiogroup"] label:hover { border-color: #0082ff; }
    div[role="radiogroup"] input:checked + div { color: #0082ff !important; }

    [data-testid="collapsedControl"] { display: none !important; }
    
    
    .map-title {
        color: #e6e6e6;
        font-size: 17px;
        font-weight: 600;
        margin: 6px 0 10px 0;
    }
    .stFormSubmitButton button {
        background-color: #0082ff !important;
        color: white !important;
        border: none !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        color: #0082ff;
        font-weight: 500;
        background-color: transparent;
        border-radius: 6px;
        padding: 6px 16px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #0082ff;
        color: white !important;
    }
    .st-c2 {
        background-color: rgb(65 147 235);
        
    }

    p, span, label, .stMarkdown { color: #cecece; }
</style>
"""

@st.cache_data
def load_dataset():
    df = pd.read_csv("data/bangladesh_district_rainfall.csv")
    df = df[df["year"]!=2026]
    return df

@st.cache_data
def load_data():
    df = load_dataset()
    agg = df.groupby(["year", "month", "district"]).agg(
        mean_rainfall=("mean_rainfall",   "mean"),
        total_rainfall=("total_rainfall", "sum"),
        max_rainfall=("max_rainfall",     "max")
    ).reset_index()
    return agg


@st.cache_resource
def load_geodata():
    districts = gpd.read_file("data/bgd_admin_boundaries.shp/bgd_admin2.shp")
    districts = districts.to_crs("EPSG:4326")
    districts = districts[["adm2_name", "geometry"]].copy()
    districts["geometry"] = districts["geometry"].simplify(
        tolerance=0.001, preserve_topology=True
    )
    geojson = json.loads(districts.to_json())
    proj = districts.to_crs("EPSG:32645")
    centroids = proj.geometry.centroid.to_crs("EPSG:4326")
    districts["centroid_lat"] = centroids.y
    districts["centroid_lon"] = centroids.x
    return districts, geojson


def get_filtered(df, year_sel, month_sel, metric_sel):
    data = df.copy()
    if year_sel != "Default":
        data = data[data["year"] == int(year_sel)]
    if month_sel != "Default":
        month_num = [k for k, v in MONTH_SHORT.items() if v == month_sel][0]
        data = data[data["month"] == month_num]
    agg = data.groupby("district")[metric_sel].mean().reset_index()
    agg[metric_sel] = agg[metric_sel].fillna(0).round(2)
    return agg


def build_title(prefix, year_sel, month_sel):
    if year_sel == "Default" and month_sel == "Default":
        return f"{prefix} (2020–2025 Average)"
    parts = []
    if month_sel != "Default":
        parts.append(month_sel)
    if year_sel != "Default":
        parts.append(str(year_sel))
    return f"{prefix} — {' '.join(parts)}"


def init_filter_state(form_key):
    if f"{form_key}_applied_year" not in st.session_state:
        st.session_state[f"{form_key}_applied_year"]   = "Default"
        st.session_state[f"{form_key}_applied_month"]  = "Default"
        st.session_state[f"{form_key}_applied_metric"] = "mean_rainfall"
        st.session_state[f"{form_key}_applied_rftype"] = "All"


def render_filter_form(form_key, df):
    init_filter_state(form_key)
    with st.form(key=form_key):
        st.markdown('<div class="filter-heading">Year</div>', unsafe_allow_html=True)
        # st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        year_sel = st.radio(
            "Year", options=["Default"] + [str(y) for y in sorted(df["year"].unique())],
            horizontal=True, label_visibility="collapsed", key=f"{form_key}_year"
        )
        st.markdown('<div class="filter-heading">Month</div>', unsafe_allow_html=True)
        # st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        month_sel = st.radio(
            "Month", options=["Default"] + list(MONTH_SHORT.values()),
            horizontal=True, label_visibility="collapsed", key=f"{form_key}_month"
        )
        st.markdown('<div class="filter-heading">Metric</div>', unsafe_allow_html=True)
        # st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        metric_sel = st.radio(
            "Metric", options=list(METRIC_LABELS.keys()),
            format_func=lambda x: METRIC_LABELS[x],
            horizontal=True, label_visibility="collapsed", key=f"{form_key}_metric"
        )
        st.markdown('<div class="filter-heading">Rainfall type (optional)</div>', unsafe_allow_html=True)
        st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        rftype_sel = st.radio(
            "Rainfall type", options=["All"] + list(RAINFALL_CATEGORIES.keys()),
            horizontal=True, label_visibility="collapsed", key=f"{form_key}_rftype"
        )
        submitted = st.form_submit_button("Apply Filter", type="primary", use_container_width=False)
        if submitted:
            st.session_state[f"{form_key}_applied_year"]   = year_sel
            st.session_state[f"{form_key}_applied_month"]  = month_sel
            st.session_state[f"{form_key}_applied_metric"] = metric_sel
            st.session_state[f"{form_key}_applied_rftype"] = rftype_sel

def get_rainfall_type(val):
    if val == 0:
        return "No precipitation"
    elif val <= 2.5:
        return "Very light"
    elif val <= 7.5:
        return "Light"
    elif val <= 35:
        return "Moderate"
    elif val <= 65:
        return "Heavy"
    else:
        return "Very heavy"
    
def render_page_header(page_name):
    maps_cls     = "nav-btn active" if page_name == "Maps"     else "nav-btn"
    analysis_cls = "nav-btn active" if page_name == "Analysis" else "nav-btn"

    st.markdown(f"""
    <style>
    .nav-bar {{
        background-color: #0d0d0d;
        border: 1px solid #262626;
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .nav-title {{ font-size: 24px; font-weight: 700; margin: 0; line-height: 38px; }}
    .nav-title .brand {{ color: #0379a8; }}
    .nav-title .sub   {{ color: #cecece; }}
    .nav-buttons {{ display: flex; gap: 8px; }}
    .nav-btn {{
        background: transparent;
        color: #0082ff;
        border: 1px solid #0082ff;
        border-radius: 6px;
        padding: 6px 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
    }}
    .nav-btn:hover  {{ background: #0082ff; color: white; }}
    .nav-btn.active {{ background: #0082ff; color: white; }}
    </style>
    <div class="nav-bar">
        <div class="nav-title">
            <span class="brand">BD Raindrop</span>
            <span class="sub"> Dashboard</span>
        </div>

    </div>
    """, unsafe_allow_html=True)

MAP_ICON_SVG = """
<svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-bottom:12px;">
    <polygon points="2,8 16,4 32,12 46,6 46,40 32,46 16,38 2,44" fill="none" stroke="#0082ff" stroke-width="1.5" stroke-linejoin="round"/>
    <line x1="16" y1="4" x2="16" y2="38" stroke="#0082ff" stroke-width="1.5"/>
    <line x1="32" y1="12" x2="32" y2="46" stroke="#0082ff" stroke-width="1.5"/>
    <circle cx="24" cy="22" r="4" fill="none" stroke="#0379a8" stroke-width="1.5"/>
    <line x1="24" y1="26" x2="24" y2="34" stroke="#0379a8" stroke-width="1.5" stroke-linecap="round"/>
</svg>
"""