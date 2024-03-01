if "encoded_categorical_vars" in locals() and "normalized_continuous_vars" in locals():
    X = pd.concat([normalized_continuous_vars, encoded_categorical_vars], axis=1)
    st.text(f"{models['H2'].predict(X)}")
    H2 = denormalize(models["H2"].predict(X), target_data["H2"])
    CO2 = denormalize(models["CO2"].predict(X), target_data["CO2"])
    st.text(f"{H2, CO2}")
