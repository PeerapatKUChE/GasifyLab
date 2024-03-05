import streamlit as st
from datetime import datetime

st.title("Feedback")

# datetime object containing current date and time
now = datetime.now()
 
st.write("now =", now)

# dd/mm/YY H:M:S
dt_string1 = now.strftime("%d/%m/%Y")
dt_string2 = now.strftime("%H:%M:%S")
st.write("date and time =", dt_string1, "time:" dt_string2)
