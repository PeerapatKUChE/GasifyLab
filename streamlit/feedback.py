import streamlit as st

st.title("Feedback")

from trubrics.integrations.streamlit import FeedbackCollector

collector = FeedbackCollector()
collector.st_feedback(feedback_type="issue")

collector.st_feedback(feedback_type="faces")
