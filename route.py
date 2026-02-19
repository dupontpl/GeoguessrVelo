import os
import osmnx as ox
import geopandas as gpd
import time

# =========================
# CONFIG
# =========================

GEOJSON_PATH = "departements.geojson"
OUTPUT_DIR = "routes"

# mettre {"38"} pour Isère seulement
ONLY_DEPTS = {}     # ← {} = tous
RESUME_MODE = True
SLEEP_BETWEEN = 5       # secondes entre requêtes OSM

BAD_HIGHWAY = {
    "motorway",
    "trunk",
    "primary",
    "motorway_link",
    "trunk_link",
    "primary_link"
}

# routes goudronnées seulement
SURFACE_REGEX = "asphalt|paved|concrete|paving_stones"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# LOAD DEPARTEMENTS
# =========================

gdf = gpd.read_file(GEOJSON_PATH)
print("Départements chargés :", len(gdf))

# =========================
# LOOP
# =========================

for _, row in gdf.iterrows():

    code = str(row["code"])
    nom = row["nom"]
    geom = row.geometry

    if ONLY_DEPTS and code not in ONLY_DEPTS:
        continue

    out_path = f"{OUTPUT_DIR}/routes_{code}.parquet"

    if RESUME_MODE and os.path.exists(out_path):
        print(f"SKIP déjà fait → {nom} ({code})")
        continue

    print(f"\n==============================")
    print(f"{nom} ({code})")
    print("==============================")

    try:

        # -------------------------
        # FILTRE OSM GOUDRONNÉ
        # -------------------------
        custom_filter = f"""
        ["highway"]
        ["surface"~"{SURFACE_REGEX}"]
        """

        print("Téléchargement OSM (paved only)...")

        G = ox.graph_from_polygon(
            geom,
            custom_filter=custom_filter,
            simplify=True
        )

        edges = ox.graph_to_gdfs(G, nodes=False)

        print("Segments téléchargés :", len(edges))

        # -------------------------
        # FILTRE TYPES ROUTES
        # -------------------------
        def is_bad(hw):
            if isinstance(hw, list):
                return any(h in BAD_HIGHWAY for h in hw)
            return hw in BAD_HIGHWAY

        edges = edges[~edges["highway"].apply(is_bad)]

        print("Segments après filtre :", len(edges))

        if len(edges) == 0:
            print("⚠️ Aucun segment gardé — skip")
            continue

        # -------------------------
        # COLONNES UTILES
        # -------------------------
        edges = edges[["geometry"]].copy()
        edges["dept"] = code

        # -------------------------
        # SAVE
        # -------------------------
        edges.to_parquet(out_path)

        print("✅ Sauvé →", out_path)

        # -------------------------
        # RATE LIMIT SAFE
        # -------------------------
        time.sleep(SLEEP_BETWEEN)

    except Exception as e:
        print("❌ ERREUR :", e)
