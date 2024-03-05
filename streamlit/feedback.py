import streamlit as st
from datetime import datetime

st.title("Feedback")
st.write("We appreciate your commitment to improving our platform! Your feedback and bug reports are invaluable in helping us enhance the user experience and address any issues promptly. Please use the form below to share your thoughts or report any bugs you may have encountered.")

st.text_input("Subject")
st.text_area("Description")
now = datetime.now()

st.write("now =", now)

# dd/mm/YY H:M:S
dt_string1 = now.strftime("%d/%m/%Y")
dt_string2 = now.strftime("%H:%M:%S")
st.write("date and time =", dt_string1, "time:", dt_string2)
