import os
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

url = "https://docs.google.com/spreadsheets/d/1JbyaF0-QGG9EsgELp3qIG6HJvE_xDbCM0hmKBlRnjf4/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

data = conn.read(spreadsheet=url, worksheet="Feedback")
st.dataframe(data)

st.title("Feedback")
st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur semper pharetra aliquet. In facilisis, velit a molestie sollicitudin, nisl tellus sagittis eros, vel vehicula est elit nec odio. Vivamus luctus, tortor at scelerisque congue, metus neque suscipit lectus, bibendum ultrices nisi mi sed ex. Mauris aliquet eros sit amet pellentesque.")
st.write(":red[* Required]")

feedback = pd.read_csv(os.path.dirname(__file__) + "/feedback.csv").drop(columns=["Unnamed: 0"])

with st.form("Feedback Form", clear_on_submit=True, border=False):
    subject = st.text_input("Subject :red[*]", value=None)
    message = st.text_area("Message :red[*]", value=None)
    attachments = st.text_input("Attachment link(s) :gray[(optional)]", value=None)

    if st.form_submit_button("Submit"):
        if subject != None and message != None:
            now = datetime.now()
            date = now.strftime("%d/%m/%Y")
            time = now.strftime("%H:%M:%S")

            latest_feedback = pd.DataFrame({
                "Date": date,
                "Time": time,
                "Subject": subject,
                "Message": message,
                "Attachment(s)": attachments
            }, index=[feedback.shape[0]])

            feedback = pd.concat([feedback, latest_feedback])

            conn.update(spreadsheet=url, worksheet="Feedback", data=feedback)

            st.success("Your feedback has been submitted successfully.")

        if subject is None:
            st.error("Error: Subject cannot be blank.")
        if message is None:
            st.error("Error: Message cannot be blank.")
