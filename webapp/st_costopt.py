import os
import pulp
import streamlit as st
import numpy as np
import pandas as pd

def load_data(path):
    compositions = pd.read_excel(path+"/data/raw/Data-ThaiBiomassComposition.xlsx", sheet_name="Processed Data")
    densities = pd.read_excel(path+"/data/raw/Data-ThaiBiomass.xlsx", sheet_name="Biomass Cost")
    supplies = pd.read_excel(path+"/data/raw/Data-ThaiBiomass.xlsx", sheet_name="Biomass Data")
    distances = pd.read_excel(path+"/data/raw/Data-Distances.xlsx")
    return compositions, supplies, distances

def calculate_transportation_cost(
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height,
        cargo_capacity, densities
):
    fuel_consumption_cost = fuel_price / fuel_consumption_rate
    average_tire_cost_per_km = tire_price * number_of_tires / tire_lifespan
    total_variable_cost = fuel_consumption_cost + average_tire_cost_per_km + maintenance_cost
    cargo_volume = cargo_width * cargo_length * cargo_height

    transportation_costs_df = pd.DataFrame()
    for i in range(densities.shape[0]):
        weight_at_max_volume = densities.iloc[i] * cargo_volume / 1000
        weight_at_max_capacity = min(weight_at_max_volume, cargo_capacity)
        transportation_cost = total_variable_cost / weight_at_max_capacity
        transportation_cost = pd.DataFrame([transportation_cost], index=[i])
        transportation_costs_df = pd.concat([transportation_costs_df, transportation_cost])

    return transportation_costs_df

def prepare_data(
        target_composition, compositions, prices, densities, supplies, distances,
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height, cargo_capacity
    ):
    
    biomass_data = compositions.merge(prices, on="Biomass Type")
    biomass_data = biomass_data.merge(densities[["Biomass Type", "Density"]], on="Biomass Type")
    st.dataframe(biomass_data)
    biomass_data["Transportation Cost"] = calculate_transportation_cost(
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height,
        cargo_capacity, biomass_data["Density"]
    )
    biomass_data = biomass_data.drop(columns=["Density"])
    biomass_data = biomass_data.sort_values(by=["Biomass Type"])

    st.dataframe(biomass_data)

    supplies = supplies.drop(columns=["No.", "Region"])
    S = supplies.T
    S.columns = supplies["Province"]
    S = S.sort_index(axis=0)
    S = S.sort_index(axis=1)
    S = S.drop(["Province"])
    S.columns.names = [""]

    distances = distances.drop(columns=["Latitude", "Longitude"])
    D = distances.drop(columns=["Plant Code"])
    D.index = distances["Plant Code"]
    D = D.sort_index(axis=0)
    D = D.sort_index(axis=1)
    D.index.names = [""]

    Nb = S.shape[0]
    Ns = D.shape[1]
    Ng = D.shape[0]
    C = biomass_data["C"]
    H = biomass_data["H"]
    A = biomass_data["Ash"]
    Ct = target_composition["Target carbon"]
    Ht = target_composition["Target hydrogen"]
    At = target_composition["Target ash"]
    F = biomass_data["Feedstock Cost"]
    T = biomass_data["Transportation Cost"]

    return Nb, Ns, Ng, C, H, A, Ct, Ht, At, F, T, D, S

def milp_solver(
        target_composition, compositions, prices, supplies, distances,
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height, cargo_capacity
    ):

    Nb, Ns, Ng, C, H, A, Ct, Ht, At, F, T, D, S = prepare_data(
        target_composition, compositions, prices, supplies, distances,
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height, cargo_capacity
        )
    return

def main():
    compositions, densities, supplies, distances = load_data(os.path.abspath(os.curdir))

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
        biomass_prices = {
            "Biomass Type": [
                "Cassava rhizome", "Coconut coir", "Coconut shell", "Corn stalk", "Corncob",
                "Palm empty fruit bunch", "Palm frond", "Palm kernel shell", "Palm trunk", "Rice husk",
                "Rice straw", "Rubber wood sawdust", "Sugarcane bagasse", "Sugarcane leaf"
            ],
            "Price (THB/ton)": default_biomass_price
        }

        if "biomass_prices" not in st.session_state:
            biomass_prices = pd.DataFrame(biomass_prices)
            st.session_state.biomass_prices = biomass_prices
            st.session_state.key = 0
        biomass_prices = st.session_state.biomass_prices

        biomass_prices = col1.data_editor(biomass_prices, disabled=["Biomass Type"], hide_index=True, key=f"Biomass price edited #{st.session_state.key}")

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
            prepare_data(
                target_composition=target_composition,
                compositions=compositions,
                prices=biomass_prices,
                densities=densities,
                supplies=supplies,
                distances=distances,
                fuel_price=truck_params["Fuel price"],
                fuel_consumption_rate=truck_params["Fuel consumption rate"],
                maintenance_cost=truck_params["Maintenance cost"],
                tire_price=truck_params["Tire price"],
                tire_lifespan=truck_params["Tire lifespan"],
                number_of_tires=truck_params["Number of tires"],
                cargo_width=truck_params["Cargo width"],
                cargo_length=truck_params["Cargo length"],
                cargo_height=truck_params["Cargo height"],
                cargo_capacity=truck_params["Cargo capacity"]
            )
        
        def reset():
            for target_key in list(target_composition.keys()):
                st.session_state[target_key] = None
            for truck_key in list(truck_params.keys()):
                st.session_state[truck_key] = default_truck_params[truck_key]
            st.session_state.key += 1
            
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
