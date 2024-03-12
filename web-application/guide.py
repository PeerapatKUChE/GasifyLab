import streamlit as st

st.title("User Guide")
st.subheader("Getting Started")

number, text = st.columns([1, 10])
number.write("1.‎ ")
text.write("Accessing the Web App:")
number.write("‎ ")
text.write("Open your preferred web browser and navigate to [the estimation tool](https://gasifylab.streamlit.app/Estimation%20Tool).")
number.write("2.‎ ")

st.text_area("Access the Web App:
Open your web browser and go to www.biomass-estimator.com.

Homepage:
You will be directed to the homepage where you can find a brief introduction to the estimator. Click on the "Get Started" button to proceed.")

