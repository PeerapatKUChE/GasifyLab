import streamlit as st

st.title("Predict H₂ & CO₂ from Biomass Gasification")
st.text("Description")

particle_size = st.text_input("Particle size (mm) *")
carbon = st.text_input("Carbon (%daf)")
hydrogen = st.text_input("Hydrogen (%daf)")
ash = st.text_input("Ash (%db)")
moisture = st.text_input("Moisture (%wb) *")

temperature = st.text_input("Temperature (°C) *")
steam_biomass = st.text_input("Steam/biomass ratio (wt/wt)")
equivalence_ratio = st.text_input("Equivalence ratio of non-steam agent")

feedstock = st.selectbox("Feedstock", ("Herbaceous biomass", "Municipal solid waste", "Sewage sludge", "Woody biomass", "Other"), index=None, placeholder="Select")
agent = st.selectbox("Gasifying agent", ("Air", "Steam", "Air/steam", "Oxygen"), index=None, placeholder="Select")
reactor = st.selectbox("Reactor *", ("Fixed-bed", "Fluidised-bed", "Other"), index=None, placeholder="Select")
bed_material = st.selectbox("Bed material *", ("Alumina", "Olivine", "Silica"), index=None, placeholder="Select")
catalyst = st.selectbox("Catalyst presence *", ("Absent", "Present"), index=None, placeholder="Select")
scale = st.selectbox("System scale *", ("Laboratory", "Pilot"), index=None, placeholder="Select")

if particle_size == "":
    st.error("Missing particle size")
    st.focus(particle_size)

if (carbon == "" and hydrogen == "") or feedstock =="":
    st.error("Missing carbon")
    st.focus(carbon)
else:
    st.text(float(carbon)+float(hydrogen))
