import streamlit as st

st.title("Predict H₂ & CO₂ from Biomass Gasification")
st.text("Predict H₂ & CO₂ from Biomass Gasification")

particle_size = st.text_input('Particle size (mm)')
carbon = st.text_input('Carbon (%daf)')
hydrogen = st.text_input('Hydrogen (%daf)')
ash = st.text_input('Carbon (%db)')
moisture = st.text_input('Moisture (%wb)')

temperature = st.text_input('Temperature (°C)')
steam_biomass = st.text_input('Steam/biomass ratio (wt/wt)')
equivalence_ratio = st.text_input('Equivalence ratio of non-steam agent')

feedstock = st.selectbox('Feedstock', ('Herbaceous biomass', 'Municipal solid waste', 'Sewage sludge', 'Woody biomass', 'Other'))

