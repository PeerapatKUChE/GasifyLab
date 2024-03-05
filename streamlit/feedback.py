import streamlit as st
from datetime import datetime

st.title("Feedback")

# datetime object containing current date and time
now = datetime.now()
 
st.write("now =", now)

# dd/mm/YY H:M:S
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
st.write("date and time =", dt_string)
