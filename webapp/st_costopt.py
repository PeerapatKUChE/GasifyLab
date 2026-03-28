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

    # STEP 1: Data prep
    status_text.text("🔄 Preparing data...")
    Nb, Ns, Ng, C, H, Ct, Ht, F, T, D, S = prepare_data(
        prices, target_composition, compositions, densities, supplies, distances,
        fuel_price, fuel_consumption_rate, maintenance_cost, tire_price,
        tire_lifespan, number_of_tires, cargo_width, cargo_length, cargo_height, cargo_capacity
    )
    progress_bar.progress(10)

    # STEP 2: Model
    status_text.text("🧠 Building model...")
    prob = pulp.LpProblem("Cost_Optimization", pulp.LpMinimize)

    total_vars = Nb*Ns*Ng + Ng*Ns + Ns + Ng
    created = 0

    X = np.empty((Nb, Ns, Ng), dtype=object)
    for j in range(Nb):
        for k in range(Ns):
            for l in range(Ng):
                X[j,k,l] = pulp.LpVariable(f"X_{j}_{k}_{l}", lowBound=0)
                created += 1
                if created % 500 == 0:
                    progress_bar.progress(10 + int(created/total_vars*30))

    Y = np.empty((Ng, Ns), dtype=object)
    for l in range(Ng):
        for k in range(Ns):
            Y[l,k] = pulp.LpVariable(f"Y_{l}_{k}", cat="Binary")

    Ys = np.array([pulp.LpVariable(f"Yp_{k}", cat="Binary") for k in range(Ns)])
    Yg = np.array([pulp.LpVariable(f"Yg_{l}", cat="Binary") for l in range(Ng)])

    progress_bar.progress(40)

    # Objective
    status_text.text("📊 Setting objective...")
    FC = pulp.lpSum(X * F.values.reshape(Nb, 1, 1))
    TC = pulp.lpSum(np.sum(X * D.values.T.reshape(1, Ns, Ng), axis=2) * T.values.reshape(Nb, 1))
    prob += FC + TC
    progress_bar.progress(50)

    # Constraints
    status_text.text("📐 Adding constraints...")
    total_constraints = Nb*Ns + Ns*Ng + Ns + Ng + 5
    count = 0

    prob += pulp.lpSum(Yg) == 1; count+=1

    for k in range(Ns):
        prob += pulp.lpSum(Y[:, k]) == Ys[k]; count+=1

    for l in range(Ng):
        prob += pulp.lpSum(Y[l, :]) <= Yg[l] * Ns; count+=1

    for j in range(Nb):
        for k in range(Ns):
            prob += pulp.lpSum(X[j, k, :]) <= S.iloc[j, k]; count+=1
            if count % 200 == 0:
                progress_bar.progress(50 + int(count/total_constraints*30))

    M = 10**15
    for k in range(Ns):
        for l in range(Ng):
            prob += pulp.lpSum(X[:, k, l]) <= Y[l, k] * M

    prob += Ct * pulp.lpSum(X) == pulp.lpDot(C.values, [pulp.lpSum(X[j,:,:]) for j in range(Nb)])
    prob += Ht * pulp.lpSum(X) == pulp.lpDot(H.values, [pulp.lpSum(X[j,:,:]) for j in range(Nb)])
    prob += pulp.lpSum(X) >= min_supply
    prob += pulp.lpSum(Y) >= 1

    progress_bar.progress(80)

    # Solve
    status_text.text("⚙️ Solving...")
    with st.spinner("Running solver..."):
        status = prob.solve()

    progress_bar.progress(95)

    status_text.text("📦 Processing results...")

    if status == pulp.LpStatusOptimal:
        summary = {"Selected Plant Code": "OK"}
        selected_feedstock = pd.DataFrame([[100]], columns=["Result"])
        details = pd.DataFrame({"Status":["Success"]})
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


def main():
    st.set_page_config(layout="wide")
    st.title("Biomass Blending Dashboard")

    compositions, densities, supplies, distances = load_data(os.path.abspath(os.curdir))

    default_summary = {"Selected Plant Code": None}
    default_selected_feedstock = pd.DataFrame([[0]], columns=["No Data"])

    if st.button("Run Optimization"):
        summary, selected_feedstock, details = milp_solver(
            prices=pd.DataFrame({"Biomass Type":["a"],"Price (THB/ton)":[1]}),
            target_composition={"Target carbon":50,"Target hydrogen":6},
            compositions=compositions,
            densities=densities,
            supplies=supplies,
            distances=distances,
            fuel_price=30,
            fuel_consumption_rate=5,
            maintenance_cost=1,
            tire_price=8000,
            tire_lifespan=70000,
            number_of_tires=10,
            cargo_width=2,
            cargo_length=7,
            cargo_height=2,
            cargo_capacity=16,
            min_supply=10000,
            default_summary=default_summary,
            default_selected_feedstock=default_selected_feedstock
        )

        st.write(summary)


if __name__ == "__main__":
    main()
