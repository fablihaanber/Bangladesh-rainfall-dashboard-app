# 🌧️ BD Raindrop Dashboard

An interactive geospatial web application for visualising and analysing rainfall patterns across Bangladesh at the district level, built with Streamlit and Folium.

---

## 📌 Overview

BD Raindrop Dashboard provides district-level rainfall insights across Bangladesh using CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data) from 2020 to 2025. The dashboard is designed for researchers, data analysts, and policy makers interested in climate patterns, flood risk, and agricultural planning in Bangladesh.

---

## 🗺️ Features

### Maps Page
- **Choropleth Map** — District-level rainfall visualised using a blue gradient colormap with interactive tooltips showing district name and rainfall value. Filterable by year, month, metric, and rainfall type.
- **Heatmap** — Rainfall intensity visualised using a blue-to-red gradient over Stamen Terrain tiles, showing elevation and river networks underneath. Hovering shows district name, rainfall value, and rainfall classification.
- **Daily Rainfall Timelapse** — Animated day-by-day choropleth for a user-selected date range (max 30 days). Features a play/pause timeline slider, custom dark-themed controls, and a gradient legend.

### Analysis Page
- **Annual Mean Rainfall** — Bar chart of yearly average rainfall filterable by season
- **Max vs Min Rainfall** — Year-over-year line chart comparing extremes
- **Season Filter** — Filter all charts by Pre-Monsoon, Monsoon, Post-Monsoon, or Winter

---

## 📂 Project Structure

```
rainfall-bangladesh-app/
├── Data Preprocessing.ipynb       ← How the dataset was processed
├──app.py                          ← Entry point, page routing
├── utils.py                        ← Shared data loaders, CSS, helpers
├── styles.css                  ← Folium map custom CSS
├── requirements.txt                ← Python dependencies
├── .streamlit/
│   └── config.toml                 ← Streamlit config (hot reload)
├── pages/
│   ├── 1_Maps.py                   ← Maps page (choropleth, heatmap, timelapse)
│   └── 2_Analysis.py               ← Analysis page (charts)
├── data/
│   └── bangladesh_district_rainfall.csv
└── bgd_admin_boundaries.shp/
    └── bgd_admin2.shp              ← District-level shapefile
    └── ...
```

---

## 📊 Dataset

| Property | Details |
|---|---|
| Source | CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data) |
| Coverage | Bangladesh — 64 districts |
| Period | January 2020 — December 2025(The additional 1st jan, 2026 date is omitted) |
| Frequency | Daily |
| Columns | date, year, month, day, district, division, mean_rainfall, total_rainfall, max_rainfall, min_rainfall |

---

## 🛠️ Tech Stack

| Library | Purpose |
|---|---|
| Streamlit | Web app framework |
| Folium | Interactive Leaflet.js maps |
| streamlit-folium | Folium integration for Streamlit |
| GeoPandas | Shapefile loading and spatial operations |
| Pandas | Data wrangling |
| Plotly | Interactive charts |
| Branca | Folium colormaps and legends |
| Shapely | Geometry simplification |

---

## 🚀 Setup

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/rainfall-bangladesh-app.git
cd rainfall-bangladesh-app
```

**2. Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```


**4. Add Stadia Maps API key**

Get a free API key from [stadiamaps.com](https://stadiamaps.com) and replace `YOUR_KEY_HERE` in `pages/1_Maps.py`:
```python
tiles="https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}{r}.png?api_key=YOUR_KEY_HERE"
```
(The app runs without the key)

**5. Run the app**
```bash
streamlit run app.py
```

---

## 🗂️ Rainfall Classification

| Category | Range |
|---|---|
| No precipitation | 0 mm |
| Very light | 0 – 2.5 mm |
| Light | 2.5 – 7.5 mm |
| Moderate | 7.5 – 35 mm |
| Heavy | 35 – 65 mm |
| Very heavy | 65+ mm |

---

## 📸 Screenshots

<img width="1003" height="582" alt="image" src="https://github.com/user-attachments/assets/6af806bc-d513-4343-8ebe-199e6030fac7" />
<img width="1047" height="557" alt="image" src="https://github.com/user-attachments/assets/344d851a-3938-4b16-9aaa-a40e86844389" />


---

## 🌐 Live Demo

> Add Streamlit Cloud link here after deployment

---

## 📄 License

This project is open source and available under the Boost Software License.

---

## 🙋 Author

Built by **Fabliha** as part of a data analyst portfolio project.  
Data source: [CHIRPS](https://climateserv.servirglobal.net/map)
