import streamlit as st
import pandas as pd
import numpy as np
import os
import pulp
import plotly.express as px
from datetime import datetime

# -----------------------------
# DEFAULT CONFIG
# -----------------------------
DEFAULTS = {
    "C_target": 46.21,
    "H_target": 6.48,
    "S_min": 10000.0,
    "F": [
        1800, 5000, 1000, 1500, 500, 50, 500,
        3200, 500, 1500, 2000, 600, 500, 800
    ],
    "FP": 31.94,
    "FCR": 5.0,
    "TP": 8000.0,
    "N_tires": 10,
    "TL": 70000.0,
    "VMC": 0.60,
    "W_cargo": 2.30,
    "L_cargo": 7.20,
    "H_cargo": 2.20,
    "m_max_cargo": 16.0
}

BIOMASS_TYPES = [
    "Cassava rhizome", "Coconut coir", "Coconut shell", "Corn stalk", "Corncob",
    "Palm empty fruit bunch", "Palm frond", "Palm kernel shell", "Palm trunk",
    "Rice husk", "Rice straw", "Rubber wood sawdust",
    "Sugarcane bagasse", "Sugarcane leaf"
]

# -----------------------------
# SESSION STATE INIT
# -----------------------------
def init_session():
    if "biomass_prices" not in st.session_state:
        st.session_state.biomass_prices = pd.DataFrame({
            "Biomass Type": BIOMASS_TYPES,
            "Price (THB/tonne)": DEFAULTS["F"]
        })

    if "editor_key" not in st.session_state:
        st.session_state.editor_key = 0


# -----------------------------
# RESET FUNCTION
# -----------------------------
def reset_all():
    if "editor_key" not in st.session_state:
        st.session_state.editor_key = 0

    for key, value in DEFAULTS.items():
        if key != "F":
            st.session_state[key] = value

    st.session_state["Min Supply"] = DEFAULTS["S_min"]

    st.session_state.biomass_prices = pd.DataFrame({
        "Biomass Type": BIOMASS_TYPES,
        "Price (THB/tonne)": DEFAULTS["F"]
    })

    st.session_state.editor_key += 1


# -----------------------------
# INPUT SECTIONS
# -----------------------------
def input_requirements():
    col1, col2 = st.columns(2)

    return {
        "C_target": col1.number_input(
            "Target Carbon (% daf)", 0.01, 100.0,
            value=DEFAULTS["C_target"], key="C_target"
        ),
        "H_target": col2.number_input(
            "Target Hydrogen (% daf)", 0.01, 100.0,
            value=DEFAULTS["H_target"], key="H_target"
        ),
        "S_min": st.number_input(
            "Minimum Supply (tonnes/year)", 0.01,
            value=DEFAULTS["S_min"], key="Min Supply"
        )
    }


def input_biomass_prices():
    df = st.session_state.biomass_prices

    df = st.data_editor(
        df,
        disabled=["Biomass Type"],
        hide_index=True,
        key=f"editor_{st.session_state.editor_key}",
        use_container_width=True
    )

    st.session_state.biomass_prices = df
    return df


def input_truck_params():
    col1, col2 = st.columns(2)

    fields = [
        ("FP", "Fuel Price (THB/L)", col1),
        ("FCR", "Fuel Economy (km/L)", col2),
        ("TP", "Cost per Tire", col1),
        ("N_tires", "Tires per Vehicle", col2),
        ("TL", "Tire Life (km)", col1),
        ("VMC", "Maintenance (THB/km)", col2),
        ("W_cargo", "Cargo Width (m)", col1),
        ("L_cargo", "Cargo Length (m)", col2),
        ("H_cargo", "Cargo Height (m)", col1),
        ("m_max_cargo", "Max Payload (tonnes)", col2),
    ]

    params = {}
    for key, label, col in fields:
        params[key] = col.number_input(
            label,
            min_value=0.0,
            value=float(DEFAULTS[key]),
            key=key
        )

    return params


# -----------------------------
# VALIDATION
# -----------------------------
def validate_inputs(req, prices, truck):
    errors = []

    if prices["Price (THB/tonne)"].isnull().any():
        errors.append("All biomass prices must be filled")

    for k, v in {**req, **truck}.items():
        if v is None:
            errors.append(f"{k} is required")

    return errors


# -----------------------------
# DATA LOADING
# -----------------------------
def load_data(path):
    biomass_compositions = pd.read_excel(
        os.path.join(path, "data", "raw", "Data-ThaiBiomassComposition.xlsx"),
        sheet_name="Processed Data"
    )

    biomass_data = pd.read_excel(
        os.path.join(path, "data", "raw", "Data-ThaiBiomass.xlsx"),
        sheet_name="Biomass Cost"
    )

    biomass_supplies = pd.read_excel(
        os.path.join(path, "data", "raw", "Data-ThaiBiomass.xlsx"),
        sheet_name="Biomass Data"
    )

    plant_supplier_distances = pd.read_excel(
        os.path.join(path, "data", "raw", "Data-Distances.xlsx")
    )

    return biomass_compositions, biomass_data, biomass_supplies, plant_supplier_distances


# -----------------------------
# TRANSPORTATION COST
# -----------------------------
def calculate_unit_transport_cost(truck_params, biomass_densities):
    """
    Calculate unit transportation cost for each biomass type.
    """

    FP = float(truck_params["FP"])
    FCR = float(truck_params["FCR"])
    TP = float(truck_params["TP"])
    N_tires = int(truck_params["N_tires"])
    TL = float(truck_params["TL"])
    VMC = float(truck_params["VMC"])
    cargo_width = float(truck_params["W_cargo"])
    cargo_length = float(truck_params["L_cargo"])
    cargo_height = float(truck_params["H_cargo"])
    cargo_capacity = float(truck_params["m_max_cargo"])

    # Fuel Consumption Cost (FCC, THB/km) = Fuel Price (FP, THB/L) / Fuel Consumption Rate (FCR, km/L)
    FCC = FP / FCR

    # Tire Depreciation Cost (TD, THB/km) = Tire Price (TP, THB/tire) × Number of Tires / Tire Lifespan (TL, km)
    TD = TP * N_tires / TL

    # Total Vehicle Cost (TVC, THB/km) = FCC + TD + VMC
    TVC = FCC + TD + VMC

    # Cargo Volume (m³) = Width × Length × Height
    cargo_volume = cargo_width * cargo_length * cargo_height

    # Maximum weight by volume (tonnes) = Density (kg/m³) × Volume (m³) / 1000
    max_weight_volume = np.asarray(biomass_densities) * cargo_volume / 1000

    # Effective cargo (m_bmax, tonnes) = min(volume-limited weight, cargo capacity)
    m_bmax = np.minimum(max_weight_volume, cargo_capacity)

    # Unit Transportation Cost (THB/tkm) = Total Vehicle Cost (TVC, THB/km) / Effective cargo (m_bmax, tonnes)
    Tb = TVC / m_bmax

    return pd.Series(Tb, name="Unit Transportation Cost")


# -----------------------------
# DATA PREPARATION
# -----------------------------
def prepare_data(
        biomass_compositions,
        biomass_data,
        biomass_supplies,
        plant_supplier_distances,
        requirements,
        biomass_prices,
        truck_params
    ):

    unit_transport_cost = calculate_unit_transport_cost(
        truck_params = truck_params,
        biomass_densities = biomass_data["Density"].values
    )

    Tb = pd.concat([biomass_data["Biomass Type"], unit_transport_cost], axis=1)

    biomass_prices["Biomass Type"] = biomass_prices["Biomass Type"].str.lower()

    biomass_data = biomass_compositions[["Biomass Type", "C", "H"]].merge(
        biomass_prices,
        on="Biomass Type",
        how="left"
    )

    biomass_data = biomass_data.merge(
        Tb,
        on="Biomass Type",
        how="left"
    )

    biomass_data = biomass_data.rename(
        columns={"Price (THB/tonne)": "Unit Feedstock Cost"}
    ).sort_values(
        by="Biomass Type"
    ).reset_index(
        drop=True
    )

    biomass_data.index = list(biomass_supplies.columns)[3:]

    biomass_supplies_clean = biomass_supplies.drop(columns=["No.", "Region"]).T
    biomass_supplies_clean = biomass_supplies_clean.reset_index(drop=True)
    biomass_supplies_clean.columns = biomass_supplies_clean.iloc[0]
    biomass_supplies_clean = biomass_supplies_clean.drop(0).reset_index(drop=True)
    biomass_supplies_clean.index = list(biomass_supplies.columns)[3:]
    S = biomass_supplies_clean.sort_index()

    distance_matrix = plant_supplier_distances.drop(columns=["Latitude", "Longitude"]).sort_values(by="Plant Code").reset_index(drop=True)
    distance_matrix.index = distance_matrix["Plant Code"]
    D = distance_matrix.drop(columns=["Plant Code"])


    Nb = biomass_data.shape[0]

    Ns = S.shape[1]

    Np = D.shape[0]

    C = biomass_data["C"]

    H = biomass_data["H"]

    C_opt = requirements["C_target"]

    H_opt = requirements["H_target"]

    F = biomass_data["Unit Feedstock Cost"]

    T = biomass_data["Unit Transportation Cost"]

    S_min = requirements["S_min"]

    return Nb, Ns, Np, C, H, C_opt, H_opt, F, T, D, S, S_min


# -----------------------------
# LINEAR PROGRAM SOLVER
# -----------------------------
def lp_solver(Nb, Ns, Np, C, H, C_opt, H_opt, F, T, D, S, S_min):

    prob = pulp.LpProblem("Cost_Minimization", pulp.LpMinimize)

    # Decision variables: X[j,k,l] = biomass j from supplier k to plant l
    X = {}
    for b in range(Nb):
        for s in range(Ns):
            for p in range(Np):
                X[b, s, p] = pulp.LpVariable(f"X_{b}_{s}_{p}", lowBound=0)
    
    # Objective: Feedstock cost + transport cost
    prob += pulp.lpSum([X[b, s, p] * (F[b] + T[b] * D.iloc[p, s])
                        for b in range(Nb)
                        for s in range(Ns)
                        for p in range(Np)])

    # Constraints
    # 1. Cannot exceed supply
    for b in range(Nb):
        for s in range(Ns):
            prob += pulp.lpSum([X[b, s, p] for p in range(Np)]) <= S.iloc[b, s]

    # 2. Min supply constraint
    for p in range(Np):
        prob += pulp.lpSum([X[b, s, p] for b in range(Nb) for s in range(Ns)]) >= S_min

    # 3. Carbon and Hydrogen target
    for p in range(Np):
        prob += pulp.lpSum([C[b] * X[b, s, p] for b in range(Nb) for s in range(Ns)]) \
            == C_opt * pulp.lpSum([X[b, s, p] for b in range(Nb) for s in range(Ns)])

    for p in range(Np):
        prob += pulp.lpSum([H[b] * X[b, s, p] for b in range(Nb) for s in range(Ns)]) \
            == H_opt * pulp.lpSum([X[b, s, p] for b in range(Nb) for s in range(Ns)])

    # Solve
    status = prob.solve()

    # Result dataframe
    rows = []
    if status == pulp.LpStatusOptimal:
        biomass = C.index.tolist()
        plants = D.index.tolist()
        suppliers = S.columns.tolist()
        for b in range(Nb):
            for s in range(Ns):
                for p in range(Np):
                    val = X[b, s, p].varValue
                    if val > 0:
                        feed_cost = val * F[b]
                        transport_cost = val * T[b] * D.iloc[p, s]
                        total_cost = feed_cost + transport_cost
                        rows.append({
                            "Plant": plants[p],
                            "Biomass": biomass[b],
                            "Supplier": suppliers[s],
                            "Amount (t)": val,
                            "Feedstock Cost (THB)": feed_cost,
                            "Transportation Cost (THB)": transport_cost,
                            "Total Cost (THB)": total_cost
                        })
    else:
        st.warning("No optimal solution found.")

    return pd.DataFrame(rows).sort_values(by="Plant").reset_index(drop=True)


# -----------------------------
# MAIN APP
# -----------------------------
def main():
    st.set_page_config(layout="wide")
    st.title("Biomass Blending & Logistics Optimizer")

    init_session()

    base_path = "."  # change to folder containing 'data/raw'

    result_col, _, form_col = st.columns([0.45, 0.05, 0.50])

    # --- BEFORE THE FORM, show placeholder in result_col ---
    with result_col:
        st.info("📊 Results will appear here after you submit the form.")

    with form_col.form("main_form"):
        st.markdown(":red[* All fields are required]")

        # Section 1: Requirements
        st.subheader("Supply & Quality Requirements")
        requirements = input_requirements()
        st.divider()

        # Section 2: Biomass Prices & Truck Params
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.subheader("Feedstock Prices")
            prices = input_biomass_prices()
        with col2:
            st.subheader("Truck Parameters")
            truck_params = input_truck_params()
        st.divider()

        # Submit / Reset
        submit, reset = st.columns([0.88, 0.12])
        submitted = submit.form_submit_button("Submit", type="primary")
        reset.form_submit_button("Reset", on_click=reset_all)

        if submitted:
            errors = validate_inputs(requirements, prices, truck_params)
            if errors:
                for e in errors:
                    st.error(e)
            else:
                with result_col:
                    with st.spinner("⏳ Running optimization... please wait"):
                        
                        # Load Excel data
                        biomass_compositions, biomass_data, biomass_supplies, plant_supplier_distances = load_data(base_path)

                        # Prepare data
                        Nb, Ns, Np, C, H, C_opt, H_opt, F, T, D, S, S_min = prepare_data(
                            biomass_compositions=biomass_compositions,
                            biomass_data=biomass_data,
                            biomass_supplies=biomass_supplies,
                            plant_supplier_distances=plant_supplier_distances,
                            requirements=requirements,
                            biomass_prices=prices,
                            truck_params=truck_params
                        )

                        # Solve LP
                        results_df = lp_solver(Nb, Ns, Np, C, H, C_opt, H_opt, F, T, D, S, S_min)

                    # Aggregate biomass by amount
                    if not results_df.empty:
                        # --- Pie chart ---
                        biomass_summary = results_df.groupby("Biomass")["Amount (t)"].sum().sort_values(ascending=False)

                        fig_pie = px.pie(
                            names=biomass_summary.index,
                            values=biomass_summary.values,
                            title="Overall Biomass Composition (%)",
                            hole=0.3,
                            color_discrete_sequence=px.colors.sequential.Sunset[::-1]
                        )
                        fig_pie.update_traces(direction="clockwise")
                        result_col.plotly_chart(fig_pie, use_container_width=True)

                        # Sum costs per plant
                        plant_costs = results_df.groupby("Plant")[["Feedstock Cost (THB)", "Transportation Cost (THB)", "Total Cost (THB)"]].sum()

                        # Overall average per plant
                        avg_feed = plant_costs["Feedstock Cost (THB)"].mean()
                        avg_trans = plant_costs["Transportation Cost (THB)"].mean()
                        avg_total = plant_costs["Total Cost (THB)"].mean()

                        col1, col2, col3 = st.columns([0.36, 0.39, 0.25])

                        with col1:
                            st.metric(
                                label="Average Feedstock Cost (THB/yr)",
                                value=f"{np.ceil(avg_feed):,.0f}",
                                help="Mean annual expenditure on biomass feedstock required to supply one plant."
                            )

                        with col2:
                            st.metric(
                                label="Average Transportation Cost (THB/yr)",
                                value=f"{np.ceil(avg_trans):,.0f}",
                                help="Mean annual logistics cost to transport biomass from suppliers to a plant."
                            )

                        with col3:
                            st.metric(
                                label="Average Total Cost (THB/yr)",
                                value=f"{np.ceil(avg_total):,.0f}",
                                help="Mean combined cost of feedstock procurement and transportation for one plant per year."
                            )

                        # --- Top 3 supplying provinces ---
                        top_provinces = (
                            results_df.groupby("Supplier")["Amount (t)"]
                            .sum()
                            .sort_values(ascending=False)
                            .head(3)
                            .index.tolist()
                        )
                        result_col.subheader("Top 3 Supplying Provinces")
                        result_col.write(", ".join(top_provinces))

                        # Download button
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        csv = results_df.to_csv(index=False).encode("utf-8")
                        result_col.download_button(
                            label="Download Results as CSV",
                            data=csv,
                            file_name=f"Results-{timestamp}.csv",
                            mime="text/csv"
                        )

                    else:
                        result_col.warning("⚠️ No results to display.")


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    main()
