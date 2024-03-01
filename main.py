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

def encode_categorical_value(value, category, prefix):
    if value.lower() == "laboratory":
        value = "lab"
    value_with_prefix = np.array([f"{prefix} " + value.lower()])
    encoded_values = pd.DataFrame(
        {column: (value_with_prefix == column).astype(int) for column in category}, columns=category
    )
    return encoded_values

path = os.path.dirname(__file__)

continuous_data = pd.read_excel(f"{path}/data/preprocessed/Data-Gasification-Completed.xlsx", sheet_name="Encoded Data")
categorical_data = pd.read_excel(f"{path}/data/preprocessed/Data-Gasification-Completed.xlsx", sheet_name="Normalised Data")
target_data = continuous_data[["H2", "CO2"]]

continuous_vars = {
    var: continuous_data[var]
    for var in ["Particle size", "C", "H", "Ash", "Moisture", "Temperature", "Steam/biomass ratio", "ER"]
}

categorical_vars = {
    category: [f"{category} {variable}" for variable in categorical_data[category].unique()]
    for category in ["Feedstock type", "Operation mode", "Gasifying agent", "Reactor type", "Bed material", "Catalyst", "System scale"]
}

models = {
    "H2": load(f"{path}/models/model-H2.joblib"),
    "CO2": load(f"{path}/models/model-CO2.joblib")
}

st.title("Predict H₂ and CO₂ from Biomass Gasification")
st.text("* Required")

continuous_inputs = {
    "Particle size": st.number_input("Particle size (mm) *", value=None),
    "C": st.number_input("Carbon (%daf)", value=None),
    "H": st.number_input("Hydrogen (%daf)", value=None),
    "Ash": st.number_input("Ash (%db)", value=None),
    "Moisture": st.number_input("Moisture (%wb) *", value=None),
    "Temperature": st.number_input("Temperature (°C) *", value=None),
    "Steam/biomass ratio": st.number_input("Steam/biomass ratio (wt/wt)", value=None),
    "ER": st.number_input("Equivalence ratio of non-stream agent", value=None),
}

categorical_inputs = {
    "Feedstock type": st.selectbox(
        "Feedstock", ("Herbaceous biomass", "Municipal solid waste", "Sewage sludge", "Woody biomass", "Other"),
        index=None, placeholder="Select"),
    "Operation mode": st.selectbox("Operation mode", ("Batch", "Continuous"), index=None, placeholder="Select"),
    "Gasifying agent": st.selectbox("Gasifying agent", ("Air", "Steam", "Air/steam", "Oxygen"), index=None, placeholder="Select"),
    "Reactor type": st.selectbox("Reactor *", ("Fixed bed", "Fluidised bed", "Other"), index=None, placeholder="Select"),
    "Bed material": st.selectbox("Bed material *", ("Alumina", "Olivine", "Silica"), index=None, placeholder="Select"),
    "Catalyst": st.selectbox("Catalyst presence *", ("Absent", "Present"), index=None, placeholder="Select"),
    "System scale": st.selectbox("System scale *", ("Laboratory", "Pilot"), index=None, placeholder="Select")
}

if not any(value is None for value in categorical_inputs.values()):
    encoded_categorical_vars = pd.DataFrame()
    for category in categorical_vars.keys():
        if category != "Feedstock type":
            encoded_categorical_input = encode_categorical_value(
                value=categorical_inputs[category],
                category=categorical_vars[category],
                prefix=category
            )

            encoded_categorical_vars = pd.concat([encoded_categorical_vars, encoded_categorical_input], axis=1)

if not any(value is None for value in continuous_inputs.values()):
    #for (variable, value) in continuous_inputs.items():
        #continuous_inputs[variable] = float(value)

    normalized_continuous_vars = normalize(x=pd.DataFrame(continuous_inputs, index=[0]), x_original=pd.DataFrame(continuous_vars))

if "encoded_categorical_vars" in locals() and "normalized_continuous_vars" in locals():
    X = pd.concat([normalized_continuous_vars, encoded_categorical_vars], axis=1).reindex(columns=[
        'Particle size', 'C', 'H', 'Ash', 'Moisture',
        'Temperature', 'Steam/biomass ratio', 'ER',
        'Operation mode batch', 'Operation mode continuous',
        'Gasifying agent air', 'Gasifying agent air/steam', 'Gasifying agent oxygen', 'Gasifying agent steam',
        'Reactor type fixed bed', 'Reactor type fluidised bed', 'Reactor type other',
        'Bed material alumina', 'Bed material olivine', 'Bed material silica',
        'Catalyst absent', 'Catalyst present',
        'System scale lab', 'System scale pilot'])

    H2 = denormalize(models["H2"].predict(X), target_data["H2"])
    CO2 = denormalize(models["CO2"].predict(X), target_data["CO2"])

    H2_disp, CO2_disp = st.columns(2)
    H2_disp.metric("H₂ (vol.% db)", np.round(H2, 2))
    CO2_disp.metric("CO₂ (vol.% db)", np.round(CO2, 2))
