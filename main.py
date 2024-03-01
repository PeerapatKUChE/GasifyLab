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
    for category in ["Operation mode", "Gasifying agent", "Reactor type", "Bed material", "Catalyst", "System scale"]
}

models = {
    "H2": load(f"{path}/models/model-H2.joblib"),
    "CO2": load(f"{path}/models/model-CO2.joblib")
}

y0 = np.array([0, 0])

st.title("Biomass Gasification Product Prediction Tool")
st.text("All fields are required unless specied optional.")

particle_size = st.number_input("Particle size (mm)", value=None, min_value=0.00)
carbon, hydrogen = st.columns(2)
ash, moisture = st.columns(2)
temperature = st.number_input("Temperature (°C)", value=None, min_value=0.00)
steam_biomass, equivalence_ratio = st.columns(2)

continuous_inputs = {
    "Particle size": particle_size,
    "C": carbon.number_input("Carbon (%daf)", value=None, min_value=0.00, max_value=100.00),
    "H": hydrogen.number_input("Hydrogen (%daf)", value=None, min_value=0.00, max_value=100.0),
    "Ash": ash.number_input("Ash (%db)", value=None, min_value=0.00, max_value=100.00),
    "Moisture": moisture.number_input("Moisture (%wb)", value=None, min_value=0.00, max_value=100.00),
    "Temperature": temperature,
    "Steam/biomass ratio": steam_biomass.number_input("Steam/biomass ratio (wt/wt)", value=None, min_value=0.00),
    "ER": equivalence_ratio.number_input("Equivalence ratio of non-steam agent", value=None, min_value=0.00),
}

categorical_col1, categorical_col2 = st.columns(2)
categorical_inputs = {
    "Operation mode": categorical_col1.selectbox("Operation mode", ("Batch", "Continuous"), index=None, placeholder="Select"),
    "Gasifying agent": categorical_col2.selectbox("Gasifying agent", ("Air", "Steam", "Air/steam", "Oxygen"), index=None, placeholder="Select"),
    "Reactor type": categorical_col1.selectbox("Reactor", ("Fixed bed", "Fluidised bed", "Other"), index=None, placeholder="Select"),
    "Bed material": categorical_col2.selectbox("Bed material", ("Alumina", "Olivine", "Silica"), index=None, placeholder="Select"),
    "Catalyst": categorical_col1.selectbox("Catalyst presence", ("Absent", "Present"), index=None, placeholder="Select"),
    "System scale": categorical_col2.selectbox("System scale", ("Laboratory", "Pilot"), index=None, placeholder="Select")
}
if not any(value is None for value in categorical_inputs.values()) and not any(value is None for value in continuous_inputs.values()):
    if categorical_inputs["Gasifying agent"] == "Steam" and (continuous_inputs["Steam/biomass ratio"] == 0 or continuous_inputs["ER"] > 0):
        st.error("Error: Steam/biomass ratio cannot be 0 and ER of non-steam agent must be 0 for steam gasification.")
    elif (categorical_inputs["Gasifying agent"] == "Air" or categorical_inputs["Gasifying agent"] == "Oxygen") and (continuous_inputs["ER"] == 0 or continuous_inputs["Steam/biomass ratio"] > 0):
        st.error("Error: ER of non-steam agent cannot be 0 and steam/biomass ratio must be 0 for air or oxygen gasification.")
    else:
        encoded_categorical_vars = pd.DataFrame()
        for category in categorical_vars.keys():
            encoded_categorical_input = encode_categorical_value(
                value=categorical_inputs[category],
                category=categorical_vars[category],
                prefix=category
            )

            encoded_categorical_vars = pd.concat([encoded_categorical_vars, encoded_categorical_input], axis=1)

        normalized_continuous_vars = normalize(x=pd.DataFrame(continuous_inputs, index=[0]), x_original=pd.DataFrame(continuous_vars))

        X = pd.concat([normalized_continuous_vars, encoded_categorical_vars], axis=1).reindex(columns=[
            "Particle size", "C", "H", "Ash", "Moisture",
            "Temperature", "Steam/biomass ratio", "ER",
            "Operation mode batch", "Operation mode continuous",
            "Gasifying agent air", "Gasifying agent air/steam", "Gasifying agent oxygen", "Gasifying agent steam",
            "Reactor type fixed bed", "Reactor type fluidised bed", "Reactor type other",
            "Bed material alumina", "Bed material olivine", "Bed material silica",
            "Catalyst absent", "Catalyst present",
            "System scale lab", "System scale pilot"])

        H2 = denormalize(models["H2"].predict(X), target_data["H2"])
        CO2 = denormalize(models["CO2"].predict(X), target_data["CO2"])

        y = np.array([H2, CO2])
        st.text(y)
        st.text(y-y0)
        res1, res2, res3, reset = st.columns(4)
        res1.metric("H₂ (vol.% db)", np.round(H2, 2))
        res2.metric("CO₂ (vol.% db)", np.round(CO2, 2))
        reset.text("")
        reset.button("Reset")
