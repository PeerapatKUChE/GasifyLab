import os
import streamlit as st
import numpy as np
import pandas as pd
from joblib import load
import json

def load_data(file_path):
    return pd.read_excel(file_path, sheet_name="Encoded Data"), pd.read_excel(file_path, sheet_name="Normalised Data")

def validate_inputs(categorical_inputs, continuous_inputs):
    gasifying_agent = categorical_inputs["Gasifying agent"].lower()
    steam_conditions = gasifying_agent == "steam" and (continuous_inputs["Steam/biomass ratio"] == 0 or continuous_inputs["ER"] > 0)
    air_oxygen_conditions = gasifying_agent in ["air", "oxygen"] and (continuous_inputs["ER"] == 0 or continuous_inputs["Steam/biomass ratio"] > 0)
    air_steam_conditions = gasifying_agent == "air/steam" and (continuous_inputs["Steam/biomass ratio"] == 0 or continuous_inputs["ER"] == 0)

    if steam_conditions or air_oxygen_conditions or air_steam_conditions:
        error_message = "Error: "
        if steam_conditions:
            error_message += "Steam/biomass ratio cannot be 0 and ER of non-steam agent must be 0 for steam gasification."
        if air_oxygen_conditions:
            error_message += "ER of non-steam agent cannot be 0 and steam/biomass ratio must be 0 for air or oxygen gasification."
        if air_steam_conditions:
            error_message += "Steam/biomass ratio and ER of non-steam agent cannot be 0 for air/steam gasification."
        st.error(error_message)
        return False
    
    else:
        return True

def encode_categorical_value(value, category, prefix):
    if value.lower() == "laboratory":
        value = "lab"
    value_with_prefix = np.array([f"{prefix} " + value.lower()])
    encoded_values = pd.DataFrame(
        {column: (value_with_prefix == column).astype(int) for column in category}, columns=category
    )
    return encoded_values

def normalize(x, x_original):
    xmin = pd.DataFrame.min(x_original)
    xmax = pd.DataFrame.max(x_original)
    x_norm = (x - xmin) / (xmax - xmin)

    return x_norm.reindex(columns=x_original.columns)

def denormalize(x_norm, x_original):
    x_denorm = x_norm * (x_original.max() - x_original.min()) + x_original.min()
    return x_denorm

def predict_gasification(models, continuous_inputs, categorical_inputs, categorical_vars, continuous_vars, target_data):
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

    return H2, CO2

def main():
    with open(os.getcwd()+"/webapp/data.json", 'r') as f:
        webapp_data = json.load(f)

        st.session_state["run_count"] = webapp_data["run_count"][0]["costopt"]

    continuous_data, categorical_data = load_data(os.path.abspath(os.curdir) + "/data/preprocessed/Data-Gasification-Completed.xlsx")
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
        "H2": load(os.path.abspath(os.curdir) + "/models/model-H2.joblib"),
        "CO2": load(os.path.abspath(os.curdir) + "/models/model-CO2.joblib")
    }

    with st.form("Estimation Tool"):
        st.write(":red[All fields are required.]")
        st.write("")
        st.write("**Biomass Charecteristics**")
        particle_size = st.number_input("Particle size (mm)", value=None, min_value=0.01, key="Particle size")
        carbon, hydrogen = st.columns(2)
        ash, moisture = st.columns(2)
        st.write("")
        st.write("**Process Conditions**")
        temperature = st.number_input("Temperature (°C)", value=None, min_value=0.01, key="Temperature")
        steam_biomass, equivalence_ratio = st.columns(2)

        continuous_inputs = {
            "Particle size": particle_size,
            "C": carbon.number_input("Carbon (%daf)", value=None, min_value=0.01, max_value=100.00, key="C"),
            "H": hydrogen.number_input("Hydrogen (%daf)", value=None, min_value=0.01, max_value=100.0, key="H"),
            "Ash": ash.number_input("Ash (%db)", value=None, min_value=0.01, max_value=100.00, key="Ash"),
            "Moisture": moisture.number_input("Moisture (%wb)", value=None, min_value=0.01, max_value=100.00, key="Moisture"),
            "Temperature": temperature,
            "Steam/biomass ratio": steam_biomass.number_input("Steam/biomass ratio (wt/wt)", value=None, min_value=0.00, key="Steam/biomass ratio"),
            "ER": equivalence_ratio.number_input("Equivalence ratio (ER) of non-steam agent", value=None, min_value=0.00, key="ER"),
        }

        categorical_col1, categorical_col2 = st.columns(2)
        categorical_inputs = {
            "Operation mode": categorical_col1.selectbox("Operation mode", ("Batch", "Continuous"), index=None, placeholder="Select", key="Operation mode"),
            "Gasifying agent": categorical_col2.selectbox("Gasifying agent", ("Air", "Steam", "Air/steam", "Oxygen"), index=None, placeholder="Select", key="Gasifying agent"),
            "Reactor type": categorical_col1.selectbox("Reactor", ("Fixed bed", "Fluidised bed", "Other"), index=None, placeholder="Select", key="Reactor type"),
            "Bed material": categorical_col2.selectbox("Bed material", ("Alumina", "Olivine", "Silica"), index=None, placeholder="Select", key="Bed material"),
            "Catalyst": categorical_col1.selectbox("Catalyst presence", ("Absent", "Present"), index=None, placeholder="Select", key="Catalyst"),
            "System scale": categorical_col2.selectbox("System scale", ("Laboratory", "Pilot"), index=None, placeholder="Select", key="System scale")
        }

        submit_button, _, reset_button = st.columns([1.2, 4.9, 1])

        if submit_button.form_submit_button("**Submit**", type="primary"):
            if not any(value is None for value in categorical_inputs.values()) and not any(value is None for value in continuous_inputs.values()):
                if validate_inputs(categorical_inputs, continuous_inputs):
                    H2, CO2 = predict_gasification(models, continuous_inputs, categorical_inputs, categorical_vars, continuous_vars, target_data)

                    st.session_state['run_count'] += 1
                    webapp_data["run_count"][0]["costopt"] = st.session_state["run_count"]
                    
                    with open(os.getcwd()+"/webapp/data.json", 'w') as f:
                        json.dump(webapp_data, f, indent=4)
                    print(f"Successfully saved changes")
            
            else:
                st.error("Error: All fields are required.")

        def reset():
            for key in list(continuous_inputs.keys()) + list(categorical_inputs.keys()):
                st.session_state[key] = None
        
        reset_button.form_submit_button("**:red[Reset]**", on_click=reset, type="secondary")

        st.markdown(
            """
            <style>
            button[kind="secondaryFormSubmit"] {
                background: none;
                border: none;
                color: "primaryColor";
            }
            button[kind="secondaryFormSubmit"]:hover {
                background-color: rgb(128, 128, 128, 0.15);
                border: none;
                color: "primaryColor";
            }
            button[kind="secondaryFormSubmit"]:focus {
                background-color: rgb(128, 128, 128, 0.15); 
                border: none;
                color: "primaryColor";
            }

            </style>
            """,
            unsafe_allow_html=True,
        )

    if "H2" not in locals() and "CO2" not in locals():
        H2, CO2 = np.array([0, 0])

    res1, res2, _ = st.columns([1, 1, 2])
    res1.metric("H₂ (vol.% db)", f"{H2.item():.2f}")
    res2.metric("CO₂ (vol.% db)", f"{CO2.item():.2f}")

    st.info(f"ⓘ This app has been run {st.session_state['run_count']} time{'s' if st.session_state['run_count'] != 1 else ''}")

if __name__ == "__main__":
    main()
