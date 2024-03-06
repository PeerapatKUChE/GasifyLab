import os
import streamlit as st
import gspread
import validators
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name(os.path.dirname(__file__) + "/key/biomass-gasification-faec3b292117.json", scope)
client = gspread.authorize(credentials)
 
sheet = client.open("Web Application").worksheet("Feedback")  

st.title("Feedback")
st.write("Thank you for using [Web App Name]! We're always looking for ways to improve your experience.")
st.write("If you have any suggestions on how we can make [Web App Name] better, or if you encounter a bug or unexpected behavior, please take a moment to share it with us.")
st.write("**Your report is completely anonymous. We won't collect any personal information from you**")
st.write(":red[* Required]")

with st.form("Feedback Form", clear_on_submit=True, border=False):
    subject = st.text_input("Subject :red[*]", value=None)
    message = st.text_area("Message :red[*]", value=None)
    attachments = st.text_input("Attachment link :gray[(if any)]", value=None, placeholder="Example: https://example.com/")

    if st.form_submit_button("Submit"):
        if subject != None and message != None:
            now = datetime.now()
            date = now.strftime("%d/%m/%Y")
            time = now.strftime("%H:%M:%S")

            if attachments is None:
                attachments = "N/A"
            elif not validators.url(attachments):
                st.error("Error: The attachment link is invalid.")
            else:
                feedback = [date, time, subject, message, attachments]
                sheet.append_row(feedback)

                st.success("Your feedback has been submitted successfully.")

        if subject is None:
            st.error("Error: Subject cannot be blank.")
        if message is None:
            st.error("Error: Message cannot be blank.")
