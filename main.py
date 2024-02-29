import streamlit as st
import numpy as np
import pandas as pd
from joblib import load

import os
#os.chdir("..")
directory = os.path.abspath(os.curdir)

st.text(directory)
st.text(f"{directory}\\data\\preprocessed\\Data-Gasification-Completed")
data = pd.read_excel(f"{directory}\\data\\preprocessed\\Data-Gasification-Completed", sheet_name="Preprocessed Data")

model = {
    "H2": load("models/model-H2.joblib"),
    "CO2": load("models/model-CO2.joblib")
}

continuous_inputs = {
    "Particle size": st.text_input("Particle size (mm) *"),
    "C": st.text_input("Carbon (%daf)"),
    "H": st.text_input("Hydrogen (%daf)"),
    "Ash": st.text_input("Ash (%db)"),
    "Moisture": st.text_input("Moisture (%wb) *"),
    "Temperature": st.text_input("Temperature (°C) *"),
    "Steam/biomass ratio": st.text_input("Steam/biomass ratio (wt/wt)"),
    "ER": st.text_input("Equivalence ratio of non-stream agent"),
}

categorical_inputs = {
    "Feedstock type": st.selectbox("Feedstock", ("Herbaceous biomass", "Municipal solid waste", "Sewage sludge", "Woody biomass", "Other"), index=None, placeholder="Select"),
    "Gasifying agent": st.selectbox("Gasifying agent", ("Air", "Steam", "Air/steam", "Oxygen"), index=None, placeholder="Select"),
    "Reactor type": st.selectbox("Reactor *", ("Fixed-bed", "Fluidised-bed", "Other"), index=None, placeholder="Select"),
    "Bed material": st.selectbox("Bed material *", ("Alumina", "Olivine", "Silica"), index=None, placeholder="Select"),
    "Catalyst": st.selectbox("Catalyst presence *", ("Absent", "Present"), index=None, placeholder="Select"),
    "Scale": st.selectbox("System scale *", ("Laboratory", "Pilot"), index=None, placeholder="Select")
}
