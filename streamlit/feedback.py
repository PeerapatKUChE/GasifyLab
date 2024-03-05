import os
import pandas as pd
import streamlit as st
from datetime import datetime

st.title("Feedback")
st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur semper pharetra aliquet. In facilisis, velit a molestie sollicitudin, nisl tellus sagittis eros, vel vehicula est elit nec odio. Vivamus luctus, tortor at scelerisque congue, metus neque suscipit lectus, bibendum ultrices nisi mi sed ex. Mauris aliquet eros sit amet pellentesque.")

feedback = pd.read_csv(os.path.dirname(__file__) + "/feedback.csv").drop(columns=["Unnamed: 0"])

with st.form("Feedback Form", clear_on_submit=True, border=False):
    subject = st.text_input("Subject *")
    message = st.text_area("Message *")
    attachments = st.text_input("Attachment links (optional)", value=None)

    if st.form_submit_button("Submit"):
        now = datetime.now()
        date = now.strftime("%d/%m/%Y")
        time = now.strftime("%H:%M:%S")

        latest_feedback = pd.DataFrame({
            "Date": date,
            "Time": time,
            "Subject": subject,
            "Message": message,
            "Attachments": attachments
        }, index=[feedback.shape[0]])

        feedback = pd.concat([feedback, latest_feedback])
        st.dataframe(feedback)
        feedback.to_csv(os.path.dirname(__file__) + "/feedback.csv")
