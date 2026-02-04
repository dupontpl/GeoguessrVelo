import random
import geopandas as gpd
from shapely.geometry import Point
import streamlit as st
import folium
from streamlit_folium import st_folium

GEOJSON_PATH = "departements.geojson"

st.title("Geoguessr version vélo")

@st.cache_data
def load_data():
    return gpd.read_file(GEOJSON_PATH)

gdf = load_data()

dept_dict = {
    f"{row['nom']} ({row['code']})": str(row["code"])
    for _, row in gdf.iterrows()
}

dept_names = sorted(dept_dict.keys())


# =========================
# SESSION STATE INIT
# =========================

if "last_point" not in st.session_state:
    st.session_state.last_point = None

if "last_geom" not in st.session_state:
    st.session_state.last_geom = None


# =========================
# RANDOM POINT
# =========================

def random_point_in_department(dept_code):

    dept = gdf[gdf["code"] == dept_code]
    geometry = dept.geometry.iloc[0]

    minx, miny, maxx, maxy = geometry.bounds

    while True:
        lon = random.uniform(minx, maxx)
        lat = random.uniform(miny, maxy)

        if geometry.contains(Point(lon, lat)):
            return lat, lon, geometry


# =========================
# UI
# =========================

selected = st.selectbox(
    "Choisir un département",
    dept_names,
    index=dept_names.index("Isère (38)")
)

# --- ACTION ---
if st.button("Générer un point GPS"):
    code = dept_dict[selected]
    lat, lon, geometry = random_point_in_department(code)

    st.session_state.last_point = (lat, lon)
    st.session_state.last_geom = geometry


# =========================
# AFFICHAGE (EN DEHORS DU BOUTON)
# =========================

if st.session_state.last_point:

    lat, lon = st.session_state.last_point
    geometry = st.session_state.last_geom

    st.success(f"Point : {lat:.6f}, {lon:.6f}")

    # m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
    m = folium.Map(location=[lat, lon], zoom_start=10)
    

    # folium.GeoJson(
    #     geometry.__geo_interface__,
    # ).add_to(m)

    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        weight=2,
        fill=True,
        fill_opacity=0.9,
        popup="Point"
    ).add_to(m)

    st_folium(m, width=700, height=500)
