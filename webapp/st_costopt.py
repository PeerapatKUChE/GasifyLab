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
        st.write("Truck Operational Parameters")
        fuel_price, fuel_consumption_rate, maintenance_cost = st.columns(3)
        tire_price, tire_lifespan, number_of_tires = st.columns(3)
        cargo_width, cargo,length = st.columns(2)
        cargo_height, cargo_capacity = st.columns(2)

        st.write("Biomass Price")
        biomass_price = {
            "Biomass Type": [
                "cassava rhizome", "coconut coir", "coconut shell", "corn stalk", "corncob",
                "palm empty fruit bunch", "palm frond", "palm kernel shell", "palm trunk", "rice husk",
                "rice straw", "rubber wood sawdust", "sugarcane bagasse", "sugarcane leaf"
            ],
            "Feedstock Cost": [
                1800.00, 5000.00, 1000.00, 1500.00, 500.00, 50.00, 500.00,
                3200.00, 500.00, 1500.00, 2000.00, 600.00, 500.00, 800.00
            ]
        }

        biomass_price = pd.DataFrame(biomass_price)
        biomass_price = st.data_editor(biomass_price)

if __name__ == "__main__":
    main()
