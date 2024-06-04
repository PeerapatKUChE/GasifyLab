import os
import pulp
import streamlit as st
import numpy as np
import pandas as pd

def load_data(file_path):
    return

def calculate_transportation_cost():
    return

def main():
    with st.form("Optimization Tool"):
        col1, col2, col3 = st.columns(3)

        col1.write("**Target Composition** :red[*]")
        col2.write("‎ ")
        col3.write("‎ ")
        target_composition = {
            "Target carbon": col1.number_input("Target carbon content (%daf)", value=None, min_value=0.01, key="Target carbon"),
            "Target hydrogen": col2.number_input("Target hydrogen content (%daf)", value=None, min_value=0.01, key="Target hydrogen"),
            "Target ash": col3.number_input("Target ash content (%db)", value=None, min_value=0.01, key="Target ash")
        }

        col1.write("**Biomass Price**")
        default_biomass_price = [
            1800.00, 5000.00, 1000.00, 1500.00, 500.00, 50.00, 500.00,
            3200.00, 500.00, 1500.00, 2000.00, 600.00, 500.00, 800.00
        ]
        biomass_price = {
            "Biomass Type": [
                "Cassava rhizome", "Coconut coir", "Coconut shell", "Corn stalk", "Corncob",
                "Palm empty fruit bunch", "Palm frond", "Palm kernel shell", "Palm trunk", "Rice husk",
                "Rice straw", "Rubber wood sawdust", "Sugarcane bagasse", "Sugarcane leaf"
            ],
            "Price (THB/ton)": default_biomass_price
        }

        biomass_price = pd.DataFrame(biomass_price)
        biomass_price = col1.data_editor(biomass_price, disabled=["Biomass Type"], hide_index=True, key="Biomass price")

        col2.write("**Truck Operational Parameters**")
        col3.write("‎ ")
    
        default_truck_params = {
            "Fuel price": 31.94,
            "Fuel consumption rate": 5.00,
            "Maintenance cost": 0.60,
            "Tire price": 8000.00,
            "Tire lifespan": 70000.00,
            "Number of tires": 10,
            "Cargo width": 2.30,
            "Cargo length": 7.20,
            "Cargo height": 2.20,
            "Cargo capacity": 16.00
        }

        truck_params = {
            "Fuel price": col2.number_input("Fuel price (THB/liter)", value=default_truck_params["Fuel price"], min_value=0.00, key="Fuel price"),
            "Fuel consumption rate": col3.number_input("Fuel consumption rate (km/liter)", value=default_truck_params["Fuel consumption rate"], min_value=0.01, key="Fuel consumption rate"),
            "Maintenance cost": col2.number_input("Average maintenance cost (THB/km)", value=default_truck_params["Maintenance cost"], min_value=0.00, key="Maintenance cost"),
            "Tire price": col3.number_input("Tire price (THB/tire)", value=default_truck_params["Tire price"], min_value=0.00, key="Tire price"),
            "Tire lifespan": col2.number_input("Tire lifespan (km)", value=default_truck_params["Tire lifespan"], min_value=0.01, key="Tire lifespan"),
            "Number of tires": col3.number_input("Number of tires", value=default_truck_params["Number of tires"], min_value=0, key="Number of tires"),
            "Cargo width": col2.number_input("Cargo width (m)", value=default_truck_params["Cargo width"], min_value=0.01, key="Cargo width"),
            "Cargo length": col3.number_input("Cargo length (m)", value=default_truck_params["Cargo length"], min_value=0.01, key="Cargo length"),
            "Cargo height": col2.number_input("Cargo height (m)", value=default_truck_params["Cargo height"], min_value=0.01, key="Cargo height"),
            "Cargo capacity": col3.number_input("Cargo capacity (ton)", value=default_truck_params["Cargo capacity"], min_value=0.01, key="Cargo capacity"),
        }

        submit_button, _, reset_button = st.columns([1.2, 4.9, 1])

        if submit_button.form_submit_button("**Submit**", type="primary"):
            st.write("Yes!")
        
        def reset():
            for target_key in list(target_composition.keys()):
                st.session_state[target_key] = None
            for truck_key in list(truck_params.keys()):
                st.session_state[truck_key] = default_truck_params[truck_key]
            st.write(st.session_state["Biomass price"])
            st.write(st.session_state["Biomass price"]["edited_rows"].keys())
        
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

if __name__ == "__main__":
    main()
