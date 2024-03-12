import os
import streamlit as st
import numpy as np
import pandas as pd
from joblib import load
from st_pages import Page, show_pages

st.markdown("""
    <style>
    [data-testid=stSidebar] {
        background-color: rgb(0, 0, 0, 0);
    }
    <style>
    """, unsafe_allow_html=True)

show_pages(
    [
        Page("web-application/about.py", "About"),
        Page("main.py", "Estimation Tool"),
        Page("web-application/guide.py", "User Guide"),
        Page("web-application/feedback.py", "Feedback"),
        Page("web-application/contact.py", "Contact")
    ]
)

st.markdown("""
<section class="st-emotion-cache-1voizf0 eczjsme11" data-testid="stSidebar" aria-expanded="true" style="position: relative; user-select: auto; width: 244px; height: 728px; box-sizing: border-box; flex-shrink: 0;">
    <div data-testid="stSidebarContent" class="st-emotion-cache-6qob1r eczjsme3">
        <div class="st-emotion-cache-aiumgf eczjsme2">
            <button kind="header" data-testid="baseButton-header" class="st-emotion-cache-16u5fdf ef3psqc5">
                <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor" xmlns="http://www.w3.org/2000/svg" color="inherit" class="eyeqlp51 st-emotion-cache-1pbsqtx ex0cdmw0">
                    <path fill="none" d="M0 0h24v24H0V0z"></path>
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"></path>
                </svg>
            </button>
        </div>
        <div data-testid="stSidebarNav" class="st-emotion-cache-79elbk eczjsme10">
            <ul data-testid="stSidebarNavItems" class="st-emotion-cache-lrlib eczjsme9">
                <li>
                    <div class="st-emotion-cache-j7qwjs eczjsme7">
                        <a data-testid="stSidebarNavLink" href="https://gasifylab.streamlit.app/" class="st-emotion-cache-1c900x3 eczjsme6">
                            <span class="st-emotion-cache-9lxyvz eczjsme5">About</span>
                        </a>
                    </div>
                </li>
                <li>
                    <div class="st-emotion-cache-j7qwjs eczjsme7">
                        <a data-testid="stSidebarNavLink" href="https://gasifylab.streamlit.app/Estimation Tool" class="st-emotion-cache-iefa9s eczjsme6">
                            <span class="st-emotion-cache-1ntrxfi eczjsme5">Estimation Tool</span>
                        </a>
                    </div>
                </li>
                <li>
                    <div class="st-emotion-cache-j7qwjs eczjsme7">
                        <a data-testid="stSidebarNavLink" href="https://gasifylab.streamlit.app/Hello World" class="st-emotion-cache-1c900x3 eczjsme6">
                            <span class="st-emotion-cache-9lxyvz eczjsme5">Hello World</span>
                        </a>
                    </div>
                </li>
                <li>
                    <div class="st-emotion-cache-j7qwjs eczjsme7">
                        <a data-testid="stSidebarNavLink" href="https://gasifylab.streamlit.app/Feedback" class="st-emotion-cache-1c900x3 eczjsme6">
                            <span class="st-emotion-cache-9lxyvz eczjsme5">Feedback</span>
                        </a>
                    </div>
                </li>
                <li>
                    <div class="st-emotion-cache-j7qwjs eczjsme7">
                        <a data-testid="stSidebarNavLink" href="https://gasifylab.streamlit.app/Contact" class="st-emotion-cache-1c900x3 eczjsme6">
                            <span class="st-emotion-cache-9lxyvz eczjsme5">Contact</span>
                        </a>
                    </div>
                </li>
            </ul>
        </div>
        <div data-testid="stSidebarUserContent" class="st-emotion-cache-1n5xqho eczjsme4">
            <div class="st-emotion-cache-8atqhb ea3mdgi4">
                <div data-testid="stVerticalBlockBorderWrapper" data-test-scroll-behavior="normal" class="st-emotion-cache-0 e1f1d6gn0">
                    <div class="st-emotion-cache-1wmy9hl e1f1d6gn1">
                        <div width="196" data-testid="stVerticalBlock" class="st-emotion-cache-r2l7aq e1f1d6gn2"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div>
        <div class="" style="position: absolute; user-select: none; width: 8px; height: 100%; top: 0px; cursor: col-resize; right: -6px;">
            <div class="st-emotion-cache-1eewpqt eczjsme0"></div>
        </div>
    </div>
</section>
""")

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
    st.title("Biomass Gasification Product Estimation Tool")
    st.write("This web application uses machine learning (ML) to estimate hydrogen (H₂) and carbon dioxide (CO₂) production from biomass gasification.")
    st.write("\* db: dry basis, wb: wet basis, daf: dry ash-free basis")
    st.write(":red[All fields are required.]")

    continuous_data, categorical_data = load_data(os.path.dirname(__file__) + "/data/preprocessed/Data-Gasification-Completed.xlsx")
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
        "H2": load(os.path.dirname(__file__) + "/models/model-H2.joblib"),
        "CO2": load(os.path.dirname(__file__) + "/models/model-CO2.joblib")
    }

    with st.form("Estimation Tool"):
        particle_size = st.number_input("Particle size (mm)", value=None, min_value=0.01, key="Particle size")
        carbon, hydrogen = st.columns(2)
        ash, moisture = st.columns(2)
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

        submit_button, _, reset_button = st.columns([1, 5.1, 1])

        if submit_button.form_submit_button("**Submit**", type="primary"):
            if not any(value is None for value in categorical_inputs.values()) and not any(value is None for value in continuous_inputs.values()):
                if validate_inputs(categorical_inputs, continuous_inputs):
                    H2, CO2 = predict_gasification(models, continuous_inputs, categorical_inputs, categorical_vars, continuous_vars, target_data)

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

if __name__ == "__main__":
    main()
