import os
import streamlit as st
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.dirname(__file__) + "/key/biomass-gasification-faec3b292117.json", scope)
client = gspread.authorize(creds)
 
sheet = client.open("Web Application").worksheet("Feedback")  

st.title("Feedback")
st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur semper pharetra aliquet. In facilisis, velit a molestie sollicitudin, nisl tellus sagittis eros, vel vehicula est elit nec odio. Vivamus luctus, tortor at scelerisque congue, metus neque suscipit lectus, bibendum ultrices nisi mi sed ex. Mauris aliquet eros sit amet pellentesque.")
st.write(":red[* Required]")

with st.form("Feedback Form", clear_on_submit=True, border=False):
    subject = st.text_input("Subject :red[*]", value=None)
    message = st.text_area("Message :red[*]", value=None)
    attachments = st.file_uploader("Attachment(s) :gray[(if any)]", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

    if st.form_submit_button("Submit"):
        if subject != None and message != None:
            now = datetime.now()
            date = now.strftime("%d/%m/%Y")
            time = now.strftime("%H:%M:%S")
            st.write(attachments)
            feedback = [date, time, subject, message, attachments]
            sheet.append_row(feedback)

            st.success("Your feedback has been submitted successfully.")

        if subject is None:
            st.error("Error: Subject cannot be blank.")
        if message is None:
            st.error("Error: Message cannot be blank.")
