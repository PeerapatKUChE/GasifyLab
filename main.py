import os
import streamlit as st
import numpy as np
import pandas as pd
from joblib import load

def normalize(x, x_original):
    xmin = pd.DataFrame.min(x_original)
    xmax = pd.DataFrame.max(x_original)
    x_norm = (x - xmin) / (xmax - xmin)

    return x_norm.reindex(columns=x_original.columns)

def denormalize(x_norm, x_original):
    xmax = max(x_original)
    xmin = min(x_original)
    x_denorm = x_norm * (xmax - xmin) + xmin
    
    return x_denorm

def encode_categorical_inputs(value, category, prefix):
    value_with_prefix = np.array([f"{prefix} " + value.lower()])
    encoded_values = pd.DataFrame(
        {column: (value_with_prefix == column).astype(int) for column in category}, columns=category
    )
    return encoded_values

path = os.path.dirname(__file__)

data = pd.read_excel(f"{path}/data/preprocessed/Data-Gasification-Completed.xlsx", sheet_name="Normalised Data")

continuous_vars = {
    var: data[var]
    for var in ["Particle size", "C", "H", "Ash", "Moisture", "Temperature", "Steam/biomass ratio", "ER"]
}

categorical_vars = {
    category: [f"{category} {variable}" for variable in data[category].unique()]
    for category in ["Feedstock type", "Gasifying agent", "Operation mode", "Reactor type", "Bed material", "Catalyst", "System scale"]
}

model = {
    "H2": load(f"{path}/models/model-H2.joblib"),
    "CO2": load(f"{path}/models/model-CO2.joblib")
}

st.title("Predict H₂ and CO₂ from Biomass Gasification")
st.text("* Required")

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

st.text(continuous_inputs["Particle size"])
