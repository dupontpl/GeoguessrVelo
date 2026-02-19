import random
import os
import numpy as np
import geopandas as gpd
import streamlit as st
import folium
from shapely.geometry import box
from streamlit_folium import st_folium

# =========================
# CONFIG
# =========================

ROUTES_DIR = "routes"
DEPT_GEOJSON = "departements.geojson"
CELL_SIZE = 0.04

st.title("🚴 Point vélo aléatoire")

# =========================
# LOAD DEPARTEMENTS
# =========================

@st.cache_data
def load_depts():
    return gpd.read_file(DEPT_GEOJSON)

gdf = load_depts()

dept_dict = {
    f"{row['nom']} ({row['code']})": str(row["code"])
    for _, row in gdf.iterrows()
}

dept_names = sorted(dept_dict.keys())

selected = st.selectbox(
    "Choisir un département",
    dept_names,
    index=dept_names.index("Isère (38)") if "Isère (38)" in dept_names else 0
)

dept_code = dept_dict[selected]
ROUTES_FILE = f"{ROUTES_DIR}/routes_{dept_code}.parquet"

# =========================
# LOAD ROUTES (SI EXISTE)
# =========================

@st.cache_data
def load_routes(path):
    if os.path.exists(path):
        return gpd.read_parquet(path)
    return None

routes = load_routes(ROUTES_FILE)

# =========================
# BUILD GRID CACHE SAFE
# =========================

@st.cache_data
def build_valid_cells_from_file(path, cell_size):

    routes = gpd.read_parquet(path)

    minx, miny, maxx, maxy = routes.total_bounds

    xs = np.arange(minx, maxx, cell_size)
    ys = np.arange(miny, maxy, cell_size)

    valid_cells = []

    for x in xs:
        for y in ys:
            b = box(x, y, x+cell_size, y+cell_size)

            if routes.intersects(b).any():
                valid_cells.append(b)

    return valid_cells

if routes is not None:
    # st.write("Segments routes :", len(routes))
    valid_cells = build_valid_cells_from_file(ROUTES_FILE, CELL_SIZE)
    # st.write("Cellules avec routes :", len(valid_cells))
else:
    st.warning("⚠️ Pas de fichier routes pré-calculé → fallback point aléatoire")

# =========================
# RANDOM FUNCTIONS
# =========================

def random_point_balanced(routes, cells):

    cell = random.choice(cells)
    subset = routes[routes.intersects(cell)]
    line = subset.sample(1).geometry.iloc[0]
    p = line.interpolate(random.random(), normalized=True)

    return p.y, p.x


def random_point_in_dept(code):

    geom = gdf[gdf["code"] == code].geometry.iloc[0]
    minx, miny, maxx, maxy = geom.bounds

    while True:
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)

        if geom.contains(gpd.points_from_xy([x], [y])[0]):
            return y, x

# =========================
# SESSION STATE
# =========================

if "last_point" not in st.session_state:
    st.session_state.last_point = None

# =========================
# UI
# =========================

if st.button("🎲 Générer point au hasard"):

    if routes is not None and len(routes) > 0:
        lat, lon = random_point_balanced(routes, valid_cells)
    else:
        lat, lon = random_point_in_dept(dept_code)

    st.session_state.last_point = (lat, lon)

# =========================
# DISPLAY
# =========================

if st.session_state.last_point:

    lat, lon = st.session_state.last_point

    # st.success(f"Point : {lat:.6f}, {lon:.6f}")

    coords_str = f"{lat:.6f}, {lon:.6f}"
    # st.text_input("📋 Coordonnées GPS (copier-coller)", value=coords_str)
    st.code(coords_str, language="text")

    m = folium.Map(location=[lat, lon], zoom_start=12)

    folium.CircleMarker(
        [lat, lon],
        radius=7,
        weight=2,
        fill=True,
        fill_opacity=1
    ).add_to(m)

    st_folium(m, width=700, height=500)

    street_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
    st.link_button("👁️ Street View", street_url)
