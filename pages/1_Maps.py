import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import folium
import branca.colormap as cm
import streamlit as st
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import json

from utils import (
    SHARED_CSS, METRIC_LABELS, RAINFALL_CATEGORIES, MONTH_SHORT,
    load_data, load_geodata,
    get_filtered, build_title, render_filter_form, render_page_header,
    load_map_css,
    get_rainfall_type,
    MAP_ICON_SVG
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

# tab1, tab2 = st.tabs(["Choropleth Map", "Heatmap"])
tab1, tab2, tab3 = st.tabs(["Choropleth Map", "Heat Map", "Daily Rainfall Density Timelapse"])

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

# ── TAB 2 — HEATMAP ──────────────────────────────────────────────
with tab2:
    filter_col2, map_col2 = st.columns([1, 2.2], gap="medium")

    with filter_col2:
        render_filter_form("heatmap_form", df)

    metric  = st.session_state.heatmap_form_applied_metric
    year_s  = st.session_state.heatmap_form_applied_year
    month_s = st.session_state.heatmap_form_applied_month
    rftype  = st.session_state.heatmap_form_applied_rftype

    filtered = get_filtered(df, year_s, month_s, metric)

    if rftype != "All":
        lo, hi = RAINFALL_CATEGORIES[rftype]
        filtered = filtered[
            (filtered[metric] >= lo) &
            (filtered[metric] <= hi if hi != float("inf") else filtered[metric] >= lo)
        ]

    heat_df = districts[["adm2_name", "centroid_lat", "centroid_lon"]].merge(
        filtered, left_on="adm2_name", right_on="district", how="left"
    )
    heat_df[metric] = heat_df[metric].fillna(0)
    heat_data = [
        [row["centroid_lat"], row["centroid_lon"], row[metric]]
        for _, row in heat_df.iterrows() if row[metric] > 0
    ]

    m2 = folium.Map(
    location=[23.7, 90.4], 
    zoom_start=7, 
    tiles="CartoDB dark_matter", 
    min_zoom = 7, 
    max_zoom = 10
    )
    
    # merge rainfall values into geojson for tooltip
    tooltip_geojson = json.loads(json.dumps(geojson_data))
    
    for feature in tooltip_geojson["features"]:
        name = feature["properties"]["adm2_name"]
        val  = dict(zip(filtered["district"], filtered[metric])).get(name, 0)
        feature["properties"]["rainfall_val"]  = f"{val:.2f} mm"
        feature["properties"]["rainfall_type"] = get_rainfall_type(val)

    folium.GeoJson(
        tooltip_geojson,
        style_function=lambda feature: {
            "fillColor":   "transparent",
            "color":       "white",
            "weight":      0.5,
            "fillOpacity": 0,
        },
        hover_style={"weight": 2, "color": "white"},
        tooltip=folium.GeoJsonTooltip(
            fields=["adm2_name", "rainfall_val", "rainfall_type"],
            aliases=["District:", "Rainfall:", "Type:"],
            localize=True,
            sticky=True,
        )
    ).add_to(m2)
    
    HeatMap(
        heat_data, min_opacity=0.3, radius=40, blur=30,
        gradient={"0.2": "blue", "0.4": "cyan", "0.6": "lime", "0.8": "yellow", "1.0": "red"}
    ).add_to(m2)

    map_var = m2.get_name()
    m2.get_root().script.add_child(folium.Element(f"""
        var checkReady = setInterval(function() {{
            if (typeof {map_var} !== 'undefined') {{
                clearInterval(checkReady);
                setTimeout(function() {{
                    {map_var}.invalidateSize();
                    {map_var}.eachLayer(function(layer) {{
                        if (layer._heat) {{ layer.redraw(); }}
                    }});
                }}, 800);
            }}
        }}, 100);
    """))

    m2.get_root().html.add_child(folium.Element(f"""
      <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
          background:#1e1e1e;padding:10px;border-radius:6px;
          border:1px solid #444;font-size:13px;color:white;">
          <b>{METRIC_LABELS[metric]} Intensity</b><br>
          <div style="display:flex;align-items:center;margin-top:5px;">
              <div style="width:120px;height:12px;background:linear-gradient(to right,blue,cyan,lime,yellow,red);"></div>
          </div>
          <div style="display:flex;justify-content:space-between;width:120px;margin-top:3px;">
              <span style="font-size:10px;">Low<br>(0 mm)</span>
              <span style="font-size:10px;text-align:right;">High<br>(65+ mm)</span>
          </div>
      </div>
      """))

    with map_col2:
        title = build_title("Bangladesh Rainfall Intensity", year_s, month_s)
        st.markdown(f'<div class="map-title">{title}</div>', unsafe_allow_html=True)
        with st.spinner("Rendering heatmap..."):
            st_folium(
                m2, width=800, height=600, returned_objects=[],
                center=[23.7, 90.4], zoom=7,
                key=f"heatmap_map_{year_s}_{month_s}_{metric}_{rftype}"
            )

def rainfall_data():
  df = pd.read_csv("data/bangladesh_district_rainfall.csv")
  df = df[df["year"]!=2026]
  return df

@st.cache_data
def build_timelapse_features(from_date, to_date, metric_tl):
    raw_df = rainfall_data()
    raw_df["date"] = pd.to_datetime(raw_df["date"])
    day_df = raw_df[
        (raw_df["date"] >= pd.to_datetime(from_date)) &
        (raw_df["date"] <= pd.to_datetime(to_date))
    ].copy()

    vmax_tl = day_df[metric_tl].quantile(0.95)
    vmax_tl = float(vmax_tl) if vmax_tl > 0 else 1.0

    def val_to_color(val):
        ratio = min(val / vmax_tl, 1.0)
        if ratio < 0.2:   return "#0000ff"
        elif ratio < 0.4: return "#00ffff"
        elif ratio < 0.6: return "#00ff00"
        elif ratio < 0.8: return "#ffff00"
        else:             return "#ff0000"

    features = []
    for date, group in day_df.groupby("date"):
        lookup = dict(zip(group["district"], group[metric_tl]))
        date_str = date.strftime("%Y-%m-%d")
        for feature in geojson_data["features"]:
            name = feature["properties"]["adm2_name"]
            val  = lookup.get(name, 0)
            features.append({
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    "time": date_str,
                    "style": {
                        "fillColor":   val_to_color(val),
                        "color":       "white",
                        "weight":      0.5,
                        "fillOpacity": 0.65,
                    },
                    "popup": f"{name}: {val:.2f} mm"
                }
            })
    return features, vmax_tl

# Tab 3 - Animation
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)

    filter_col_tl, map_col2 = st.columns([1, 2.2], gap="medium")

    with filter_col_tl:
        import datetime

        raw_df     = rainfall_data()
        raw_df["date"] = pd.to_datetime(raw_df["date"])
        min_date   = raw_df["date"].min().date()
        max_date   = raw_df["date"].max().date()

        st.markdown('<div class="filter-heading">Start Date</div>', unsafe_allow_html=True)
        # st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        from_date = st.date_input("From", value=min_date,
                                  min_value=min_date, max_value=max_date,
                                  key="tl_from_date", label_visibility="visible")

        # st.markdown("<br>", unsafe_allow_html=True)
        # st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        st.markdown('<div class="filter-heading">End Date</div>', unsafe_allow_html=True)
        # st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        to_date = st.date_input("To", value=min_date + datetime.timedelta(days=6),
                                min_value=min_date, max_value=max_date,
                                key="tl_to_date", label_visibility="visible")
        
        # st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="filter-heading">Metric</div>', unsafe_allow_html=True)
        # st.markdown('<hr class="filter-underline">', unsafe_allow_html=True)
        metric_tl = st.selectbox("Metric", list(METRIC_LABELS.keys()),
                                 format_func=lambda x: METRIC_LABELS[x],
                                 key="tl_metric", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        delta = (to_date - from_date).days
        if delta <= 0:
            st.error("'To' date must be after 'From' date.")
            invalid = True
        elif delta > 30:
            st.error("Range cannot exceed 30 days.")
            invalid = True
        else:
            st.caption(f"{delta} day{'s' if delta > 1 else ''} selected.")
            invalid = False

        apply = st.button("Apply", type="primary", use_container_width=True, key="tl_apply")

    with map_col2:
        if "tl_ready" not in st.session_state:
            st.session_state.tl_ready = False

        if apply:
            if invalid:
                st.session_state.tl_ready = False
            else:
                st.session_state.tl_ready      = True
                st.session_state.tl_fd  = from_date
                st.session_state.tl_td    = to_date
                st.session_state.tl_metric_val = metric_tl

        if not st.session_state.tl_ready:
            st.markdown(f"""
            <div style="height:560px; display:flex; align-items:center; justify-content:center;
                background:#1a1a1a; border-radius:10px; border:1px solid #2e2e2e;">
                <div style="text-align:center; color:white;">
                    <div style="font-size:38px; margin-bottom:12px;">{MAP_ICON_SVG}</div>
                    <div style="font-size:15px;">Select a date range (max 30 days) and click Apply</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            fd  = st.session_state.tl_fd           
            td  = st.session_state.tl_td           
            met = st.session_state.tl_metric_val

            st.markdown(
                f'<div class="map-title">Daily Rainfall Timelapse — '
                f'{fd.strftime("%d %b %Y")} to {td.strftime("%d %b %Y")}</div>',
                unsafe_allow_html=True
            )

            progress_bar = st.progress(0, text="Preparing data...")
            progress_bar.progress(10, text="Loading rainfall data...")
            features, vmax_tl = build_timelapse_features(fd, td, met)

            progress_bar.progress(50, text="Building map...")
            m3 = folium.Map(location=[23.7, 90.4], zoom_start=7, tiles="CartoDB dark_matter", max_zoom=10, min_zoom=7)

            progress_bar.progress(70, text="Adding timelapse layer...")
            from folium.plugins import TimestampedGeoJson
            TimestampedGeoJson(
                data={"type": "FeatureCollection", "features": features},
                period="P1D",
                add_last_point=False,
                auto_play=False,
                loop=False,
                max_speed=3,
                loop_button=True,
                date_options="DD MMM YYYY",
                time_slider_drag_update=True,
            ).add_to(m3)

            progress_bar.progress(85, text="Adding legend...")
            m3.get_root().html.add_child(folium.Element(f"""
            <div style="position:fixed;top:60px;right:20px;z-index:1000;
                background:#1e1e1e;padding:10px;border-radius:6px;
                border:1px solid #444;font-size:13px;color:white;">
                <b>{METRIC_LABELS[met]}</b>
                <div style="display:flex;align-items:center;margin-top:8px;gap:6px;">
                    <span style="font-size:11px;">0</span>
                    <div style="width:120px;height:12px;background:linear-gradient(to right,blue,cyan,lime,yellow,red);border-radius:3px;"></div>
                    <span style="font-size:11px;">{round(float(vmax_tl), 1)}</span>
                </div>
            </div>
            {load_map_css()}
            """))
            progress_bar.progress(95, text="Rendering map...")
            st_folium(
                m3, width=800, height=600, returned_objects=[],
                center=[23.7, 90.4], zoom=7,
                key=f"timelapse_{fd}_{td}_{met}"
            )

            progress_bar.progress(100, text="Done!")
            progress_bar.empty()




st.caption("Source: CHIRPS 2020–2025")