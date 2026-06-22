import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import folium
import branca.colormap as cm
import streamlit as st
from streamlit_folium import st_folium
from folium.plugins import HeatMap

from utils import (
    SHARED_CSS, METRIC_LABELS, RAINFALL_CATEGORIES, MONTH_SHORT,
    load_data, load_geodata,
    get_filtered, build_title, render_filter_form, render_page_header,
)

st.set_page_config(
    page_title="Maps — BD Raindrop",
    # page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)
render_page_header("Maps")

df            = load_data()
districts, geojson_data = load_geodata()

tab1, tab2 = st.tabs(["Choropleth Map", "Heatmap"])

# ── TAB 1 — CHOROPLETH ───────────────────────────────────────────
with tab1:
    filter_col, map_col = st.columns([1, 2.2], gap="medium")

    with filter_col:
        render_filter_form("choropleth_form", df)

    metric  = st.session_state.choropleth_form_applied_metric
    year_s  = st.session_state.choropleth_form_applied_year
    month_s = st.session_state.choropleth_form_applied_month
    rftype  = st.session_state.choropleth_form_applied_rftype

    filtered = get_filtered(df, year_s, month_s, metric)

    if rftype != "All":
        lo, hi = RAINFALL_CATEGORIES[rftype]
        filtered = filtered[
            (filtered[metric] >= lo) &
            (filtered[metric] <= hi if hi != float("inf") else filtered[metric] >= lo)
        ]

    rainfall_lookup = dict(zip(filtered["district"], filtered[metric]))
    merged = geojson_data
    for feature in merged["features"]:
        name = feature["properties"]["adm2_name"]
        feature["properties"][metric] = rainfall_lookup.get(name, 0)

    vals = list(rainfall_lookup.values()) or [0]
    vmin, vmax = min(vals), max(vals) if max(vals) > 0 else 1
    colormap = cm.linear.Blues_09.scale(vmin, vmax)
    colormap.width = 150
    colormap.caption = METRIC_LABELS[metric]

    m = folium.Map(location=[23.7, 90.4], 
                   zoom_start=7, 
                   tiles="CartoDB dark_matter",
                   min_zoom = 7, 
                   max_zoom = 10)
    folium.GeoJson(
        merged,
        style_function=lambda feature: {
            "fillColor":   colormap(feature["properties"].get(metric) or 0),
            "color":       "black",
            "weight":      0.5,
            "fillOpacity": 0.75,
        },
        hover_style={"weight": 2, "fillOpacity": 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=["adm2_name", metric],
            aliases=["District:", "Rainfall (mm):"],
            localize=True, sticky=True,
        )
    ).add_to(m)
    colormap.add_to(m)
    m.get_root().html.add_child(folium.Element("""
        <style>
            .legend { position: fixed !important; top: 20px !important; right: 15px !important; bottom: auto !important; left: auto !important; color:white !important; }
            .legend text { fill: white !important; }
            .legend .caption { color: white !important; transform: translateY(3px) translateX(5px) !important;}
        </style>
    """))
    colormap.tick_labels = [round(vmin, 2), round(vmax, 2)]
    with map_col:
        title = build_title("Bangladesh Rainfall", year_s, month_s)
        st.markdown(f'<div class="map-title">{title}</div>', unsafe_allow_html=True)
        with st.spinner("Rendering map..."):
            st_folium(
                m, width=800, height=600, returned_objects=[],
                center=[23.7, 90.4], zoom=7,
                key=f"choropleth_map_{year_s}_{month_s}_{metric}_{rftype}"
            )

# # ── TAB 2 — HEATMAP ──────────────────────────────────────────────
# with tab2:
#     filter_col2, map_col2 = st.columns([1, 2.2], gap="medium")

#     with filter_col2:
#         render_filter_form("heatmap_form", df)

#     metric  = st.session_state.heatmap_form_applied_metric
#     year_s  = st.session_state.heatmap_form_applied_year
#     month_s = st.session_state.heatmap_form_applied_month
#     rftype  = st.session_state.heatmap_form_applied_rftype

#     filtered = get_filtered(df, year_s, month_s, metric)

#     if rftype != "All":
#         lo, hi = RAINFALL_CATEGORIES[rftype]
#         filtered = filtered[
#             (filtered[metric] >= lo) &
#             (filtered[metric] <= hi if hi != float("inf") else filtered[metric] >= lo)
#         ]

#     heat_df = districts[["adm2_name", "centroid_lat", "centroid_lon"]].merge(
#         filtered, left_on="adm2_name", right_on="district", how="left"
#     )
#     heat_df[metric] = heat_df[metric].fillna(0)
#     heat_data = [
#         [row["centroid_lat"], row["centroid_lon"], row[metric]]
#         for _, row in heat_df.iterrows() if row[metric] > 0
#     ]

#     m2 = folium.Map(
#         location=[23.7, 90.4], 
#       zoom_start=7, 
#       tiles="CartoDB dark_matter", 
#       min_zoom = 7, 
#       max_zoom = 10)
#     folium.GeoJson(
#       geojson_data,
#       style_function=lambda feature: {
#           "fillColor":   "transparent",
#           "color":       "white",
#           "weight":      0.5,
#           "fillOpacity": 0,
#       },
#       hover_style={"weight": 2, "color": "white"},
#       tooltip=folium.GeoJsonTooltip(
#           fields=["adm2_name"],
#           aliases=["District:"],
#           localize=True,
#           sticky=True,
#       )
#     ).add_to(m2)
    
#     HeatMap(
#         heat_data, min_opacity=0.3, radius=40, blur=30,
#         gradient={"0.2": "blue", "0.4": "cyan", "0.6": "lime", "0.8": "yellow", "1.0": "red"}
#     ).add_to(m2)

#     map_var = m2.get_name()
#     m2.get_root().script.add_child(folium.Element(f"""
#         {map_var}.whenReady(function() {{ {map_var}.invalidateSize(); }});
#     """))

#     m2.get_root().html.add_child(folium.Element(f"""
#     <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
#         background:white;padding:10px;border-radius:6px;
#         border:1px solid grey;font-size:13px;">
#         <b>{METRIC_LABELS[metric]} Intensity</b><br>
#         <div style="display:flex;align-items:center;margin-top:5px;">
#             <div style="width:120px;height:12px;background:linear-gradient(to right,blue,cyan,lime,yellow,red);"></div>
#         </div>
#         <div style="display:flex;justify-content:space-between;width:120px;">
#             <span>Low</span><span>High</span>
#         </div>
#     </div>
#     """))

#     with map_col2:
#         title = build_title("Bangladesh Rainfall Intensity", year_s, month_s)
#         st.markdown(f'<div class="map-title">{title}</div>', unsafe_allow_html=True)
#         with st.spinner("Rendering heatmap..."):
#             st_folium(
#                 m2, width=800, height=600, returned_objects=[],
#                 center=[23.7, 90.4], zoom=7,
#                 key=f"heatmap_map_{year_s}_{month_s}_{metric}_{rftype}"
#             )


@st.cache_data
def build_timelapse_features(from_year, to_year, from_month, to_month, metric_tl):
    raw_df = pd.read_csv("bangladesh_district_rainfall.csv")
    raw_df["date_key"] = raw_df["year"] * 100 + raw_df["month"]
    from_key = from_year * 100 + from_month
    to_key   = to_year   * 100 + to_month

    day_df = raw_df[
        (raw_df["date_key"] >= from_key) &
        (raw_df["date_key"] <= to_key)
    ].groupby(["year", "month", "district"])[metric_tl].mean().reset_index()

    vmax_tl = day_df[metric_tl].quantile(0.95)
    vmax_tl = vmax_tl if vmax_tl > 0 else 1
    colormap_tl = cm.linear.Blues_09.scale(0, vmax_tl)

    features = []
    for (year, month), group in day_df.groupby(["year", "month"]):
        lookup   = dict(zip(group["district"], group[metric_tl]))
        date_str = f"{year}-{month:02d}-01"
        for feature in geojson_data["features"]:
            name = feature["properties"]["adm2_name"]
            val  = lookup.get(name, 0)
            features.append({
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    "time": date_str,
                    "style": {
                        "fillColor":   colormap_tl(val),
                        "color":       "black",
                        "weight":      0.5,
                        "fillOpacity": 0.75,
                    },
                    "popup": f"{name}: {val:.2f} mm"
                }
            })
    return features, colormap_tl


with tab2:
    st.markdown("<br>", unsafe_allow_html=True)

    filter_col_tl, map_col2 = st.columns([1, 2.2], gap="medium")

    with filter_col_tl:
        st.markdown('<div class="filter-heading">From</div>', unsafe_allow_html=True)
        st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        raw_df     = pd.read_csv("bangladesh_district_rainfall.csv")
        years      = sorted(raw_df["year"].unique())
        from_year  = st.selectbox("Year",  years, index=0, key="from_year")
        from_month = st.selectbox("Month", list(MONTH_SHORT.keys()),
                                  format_func=lambda x: MONTH_SHORT[x], index=0, key="from_month")
        metric_tl  = st.selectbox("Metric", list(METRIC_LABELS.keys()),
                                  format_func=lambda x: METRIC_LABELS[x], key="tl_metric")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="filter-heading">To</div>', unsafe_allow_html=True)
        st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        to_year    = st.selectbox("Year",  years, index=len(years)-1, key="to_year")
        to_month   = st.selectbox("Month", list(MONTH_SHORT.keys()),
                                  format_func=lambda x: MONTH_SHORT[x], index=11, key="to_month")

        st.markdown("<br>", unsafe_allow_html=True)
        apply = st.button("Apply", type="primary", use_container_width=True, key="tl_apply")
        invalid = (from_year, from_month) >= (to_year, to_month)

    with map_col2:
        if "tl_ready" not in st.session_state:
            st.session_state.tl_ready = False

        if apply:
          if invalid:
              st.warning("'From' must be before 'To'.")
              st.session_state.tl_ready = False
          else:
              st.session_state.tl_ready      = True
              st.session_state.tl_from_year  = from_year
              st.session_state.tl_from_month = from_month
              st.session_state.tl_to_year    = to_year
              st.session_state.tl_to_month   = to_month
              st.session_state.tl_metric_val = metric_tl  # ← renamed from tl_metric

        if not st.session_state.tl_ready:
            st.markdown("""
            <div style="height:560px; display:flex; align-items:center; justify-content:center;
                background:#1a1a1a; border-radius:10px; border:1px solid #2e2e2e;">
                <div style="text-align:center; color:#555;">
                    <div style="font-size:36px; margin-bottom:12px;">🗺️</div>
                    <div style="font-size:15px;">Select a date range and click Apply</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            fy  = st.session_state.tl_from_year
            fm  = st.session_state.tl_from_month
            ty  = st.session_state.tl_to_year
            tm  = st.session_state.tl_to_month
            met = st.session_state.tl_metric_val

            st.markdown(
                f'<div class="map-title">Monthly Rainfall Timelapse — '
                f'{MONTH_SHORT[fm]} {fy} to {MONTH_SHORT[tm]} {ty}</div>',
                unsafe_allow_html=True
            )

            progress_bar = st.progress(0, text="Preparing data...")

            progress_bar.progress(10, text="Loading rainfall data...")
            features, colormap_tl = build_timelapse_features(fy, ty, fm, tm, met)

            progress_bar.progress(50, text="Building map...")
            m3 = folium.Map(location=[23.7, 90.4], zoom_start=7, tiles="CartoDB positron")

            progress_bar.progress(70, text="Adding timelapse layer...")
            from folium.plugins import TimestampedGeoJson
            TimestampedGeoJson(
                data={"type": "FeatureCollection", "features": features},
                period="P1M",
                add_last_point=False,
                auto_play=False,
                loop=False,
                max_speed=2,
                loop_button=True,
                date_options="MMMM YYYY",
                time_slider_drag_update=True,
            ).add_to(m3)

            progress_bar.progress(85, text="Adding legend...")
            colormap_tl.caption = METRIC_LABELS[met]
            colormap_tl.width   = 150
            colormap_tl.add_to(m3)

            progress_bar.progress(95, text="Rendering map...")
            st_folium(
                m3, width=700, height=560, returned_objects=[],
                center=[23.7, 90.4], zoom=7,
                key=f"timelapse_{fy}_{fm}_{ty}_{tm}_{met}"
            )

            progress_bar.progress(100, text="Done!")
            progress_bar.empty()

st.caption("Source: CHIRPS 2020–2025")