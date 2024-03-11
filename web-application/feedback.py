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

st.title("Your Feedback Matters!")
st.write("Thank you for taking the time to share your feedback! Your input helps us improve our web application and provide the best possible experience for our users.")
st.write("This form is **completely anonymous**. Your personal information will not be collected or associated with your feedback.")
st.write("If you have a specific question, request, or need help with something beyond reporting an issue or sharing feedback, please visit our [contact page](https://gasifylab.streamlit.app/Contact).")
st.write(":red[* Required]")

with st.form("Feedback Form", clear_on_submit=True, border=False):
    subject = st.text_input("Subject :red[*]", value=None)
    message = st.text_area("Message :red[*]", value=None)
    attachments = st.text_input("Attachment link :gray[(if any)]", value=None, placeholder="Example: https://example.com/")

    if st.form_submit_button("Submit", type="secondary"):
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
