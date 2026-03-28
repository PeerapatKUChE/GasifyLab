import os
import time
import pulp
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def load_data(path):
    compositions = pd.read_excel(path+"/data/raw/Data-ThaiBiomassComposition.xlsx", sheet_name="Processed Data")
    densities = pd.read_excel(path+"/data/raw/Data-ThaiBiomass.xlsx", sheet_name="Biomass Cost")
    supplies = pd.read_excel(path+"/data/raw/Data-ThaiBiomass.xlsx", sheet_name="Biomass Data")
    distances = pd.read_excel(path+"/data/raw/Data-Distances.xlsx")
    return compositions, densities, supplies, distances

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
        prices, target_composition, compositions, densities, supplies, distances,
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height, cargo_capacity
    ):
    
    prices["Biomass Type"] = prices["Biomass Type"].str.lower()
    biomass_data = compositions.merge(prices, on="Biomass Type")
    biomass_data = biomass_data.merge(densities[["Biomass Type", "Density"]], on="Biomass Type")

    biomass_data["Transportation Cost"] = calculate_transportation_cost(
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height,
        cargo_capacity, biomass_data["Density"]
    )
    biomass_data = biomass_data.drop(columns=["Density"])
    biomass_data = biomass_data.sort_values(by=["Biomass Type"])

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
    Ct = target_composition["Target carbon"]
    Ht = target_composition["Target hydrogen"]
    F = prices["Price (THB/ton)"]
    T = biomass_data["Transportation Cost"]

    return Nb, Ns, Ng, C, H, Ct, Ht, F, T, D, S

def milp_solver(
        prices, target_composition, compositions, densities, supplies, distances,
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height, cargo_capacity,
        min_supply, default_summary, default_selected_feedstock
    ):

    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.text("🔄 Preparing data...")
    Nb, Ns, Ng, C, H, Ct, Ht, F, T, D, S = prepare_data(
        prices, target_composition, compositions, densities, supplies, distances,
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height, cargo_capacity
    )
    progress_bar.progress(15)

    status_text.text("🧠 Building optimization model...")
    prob = pulp.LpProblem("Cost_Optimization", pulp.LpMinimize)

    X = np.array([
        pulp.LpVariable(f"X_{j}_{k}_{l}", lowBound=0)
        for j in range(Nb)
        for k in range(Ns)
        for l in range(Ng)
    ]).reshape(Nb, Ns, Ng)

    Y = np.array([
        pulp.LpVariable(f"Y_{l}_{k}", cat="Binary")
        for l in range(Ng)
        for k in range(Ns)
    ]).reshape(Ng, Ns)

    Ys = np.array([pulp.LpVariable(f"Yp_{k}", cat="Binary") for k in range(Ns)]).reshape(1, Ns)
    Yg = np.array([pulp.LpVariable(f"Yg_{l}", cat="Binary") for l in range(Ng)]).reshape(Ng, 1)

    progress_bar.progress(35)

    status_text.text("📊 Setting objective function...")
    FC = pulp.lpSum(X * F.values.reshape(Nb, 1, 1))
    TC = pulp.lpSum(np.sum(X * D.values.T.reshape(1, Ns, Ng), axis=2) * T.values.reshape(Nb, 1))
    prob += FC + TC
    progress_bar.progress(50)

    status_text.text("📐 Adding constraints...")

    prob += pulp.lpSum(Yg) == 1

    for k in range(Ns):
        prob += pulp.lpSum(Y[:, k]) == Ys[0, k]

    for l in range(Ng):
        prob += pulp.lpSum(Y[l, :]) <= Yg[l, 0] * Ns

    for j in range(Nb):
        for k in range(Ns):
            prob += pulp.lpSum(X[j, k, :]) <= S.iloc[j, k]

    M = 10**15
    for k in range(Ns):
        for l in range(Ng):
            prob += pulp.lpSum(X[:, k, l]) <= Y[l, k] * M

    prob += Ct * pulp.lpSum(X) == pulp.lpDot(C.values, [pulp.lpSum(X[j, :, :]) for j in range(Nb)])
    prob += Ht * pulp.lpSum(X) == pulp.lpDot(H.values, [pulp.lpSum(X[j, :, :]) for j in range(Nb)])
    prob += pulp.lpSum(X) >= min_supply
    prob += pulp.lpSum(Y) >= 1

    progress_bar.progress(70)

    status_text.text("⚙️ Solving optimization model (this may take a while)...")
    with st.spinner("Running solver..."):
        status = prob.solve()

    progress_bar.progress(90)

    status_text.text("📦 Processing results...")

    if status == pulp.LpStatusOptimal:

        details = pd.DataFrame()

        Yg_val = np.array([Yg[l, 0].value() for l in range(Ng)]).reshape(Ng, 1)
        Yg_val = pd.DataFrame(Yg_val, index=distances["Plant Code"])
        plant = Yg_val[Yg_val == 1].dropna()

        X_val = np.array([X[j, k, l].value()
                          for j in range(Nb)
                          for k in range(Ns)
                          for l in range(Ng)]).reshape(Nb, Ns, Ng)

        X_val = np.sum(X_val, axis=2)
        X_val = pd.DataFrame(X_val, columns=D.columns, index=S.index)

        supplier_indices = X_val.any(axis=0)
        supply = X_val.loc[:, supplier_indices].T

        supplier = pd.DataFrame(supply.index, columns=["Province"], index=range(supply.shape[0]))
        details = pd.concat([details, supplier], axis=0)

        distance = D.loc[plant.index, supply.index].T
        distance.index = range(supply.shape[0])
        distance.columns = ["Distance (km)"]
        details = pd.concat([details, distance], axis=1)

        supply = supply.loc[:, (supply != 0).any(axis=0)]
        supply.index = range(supply.shape[0])
        supply.rename(columns=lambda x: x.capitalize()+" supply (ton/year)", inplace=True)
        details = pd.concat([details, supply], axis=1)

        selected_plant_code = plant.index.values[0]

        feedstock_cost = FC.value()
        transport_cost = TC.value()
        total_cost = feedstock_cost + transport_cost

        total_distance = distance.sum().values[0]
        total_supply = X_val.T.sum().sum()

        biomass_percentage = X_val.T.sum() / total_supply * 100
        selected_feedstock = pd.DataFrame(biomass_percentage[biomass_percentage > 0]).T

        summary = {
            "Selected Plant Code": selected_plant_code,
            "Total Cost (×10³ THB/year)": f"{total_cost/10**3:,.2f}",
            "Feedstock Cost (×10³ THB/year)": f"{feedstock_cost/10**3:,.2f}",
            "Transportation Cost (×10³ THB/year)": f"{transport_cost/10**3:,.2f}",
            "Total Distance (km)": f"{total_distance:,.2f}",
            "Total Supply (ton/year)": f"{total_supply:,.2f}"
        }

    else:
        summary = default_summary
        selected_feedstock = default_selected_feedstock
        details = None

    progress_bar.progress(100)
    status_text.text("✅ Done!")

    time.sleep(0.5)
    progress_bar.empty()
    status_text.empty()

    return summary, selected_feedstock, details
