import ee
import geemap.foliumap as geemap
import streamlit as st
import numpy as np

# -----------------------------
#  Initialize Earth Engine
# -----------------------------
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

st.title("🌍 PDR Calculator from Selected Area")

# -----------------------------
#  Streamlit Map
# -----------------------------
st.subheader("Select an area from the map")
m = geemap.Map(center=[23.7, 90.4], zoom=7)

# Add drawing tools
m.add_draw_control()

# Display map
m.to_streamlit(height=500)

# Button to process
if st.button("Process Selected Area"):

    # -----------------------------
    #  Get Selected Geometry
    # -----------------------------
    geom = m.user_roi

    if geom is None:
        st.error("❗ Please draw a polygon on the map first.")
        st.stop()

    st.success("Area Selected ✔")

    # -----------------------------
    #  Load Sentinel-2 (B11, NDVI)
    # -----------------------------
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR")
        .filterBounds(geom)
        .filterDate("2023-01-01", "2023-12-31")
        .sort("CLOUDY_PIXEL_PERCENTAGE")
        .first()
    )

    B11 = s2.select("B11")
    ndvi = s2.normalizedDifference(["B8", "B4"]).rename("NDVI")

    # -----------------------------
    #  LULC (ESA WorldCover 2021)
    # -----------------------------
    lulc = (
        ee.Image("ESA/WorldCover/v200/2021")
        .select("Map")
        .rename("LULC")
    )

    # -----------------------------
    #  Calculate Denitrification Rate (PDR)
    #  Example formula (You can change):
    #  PDR = (NDVI * 0.6) + (B11 * 0.4)
    # -----------------------------
    pdr = ndvi.multiply(0.6).add(B11.multiply(0.4)).rename("PDR")

    # Merge all layers
    final = B11.addBands(ndvi).addBands(lulc).addBands(pdr)

    st.success("Data Extracted Successfully ✔")

    # -----------------------------
    #  Visualization
    # -----------------------------
    st.subheader("PDR (Potential Denitrification Rate) Map")

    m2 = geemap.Map()
    m2.addLayer(pdr, {"min": -1, "max": 1}, "PDR")
    m2.to_streamlit(height=500)

    # -----------------------------
    #  Export as GeoTIFF
    # -----------------------------
    st.subheader("Download Output")

    url = final.clip(geom).getDownloadURL({
        "scale": 20,
        "crs": "EPSG:4326",
        "region": geom
    })

    st.download_button(
        label="⬇ Download GeoTIFF",
        data="Download the file from:\n" + url,
        file_name="pdr_output_url.txt"
    )

    st.info("⚠ Direct GeoTIFF download must be done from the provided URL (Earth Engine).")

