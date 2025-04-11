import streamlit as st

# Initialize the run count in session state if it doesn't exist
if 'run_count' not in st.session_state:
    st.session_state['run_count'] = 0

def increment_run_count():
    st.session_state['run_count'] += 1

st.title("Run Count Example")

if st.button("Submit", on_click=increment_run_count):
    st.write("Button clicked!")

st.write(f"Number of times the app has run since the last reload: {st.session_state['run_count']}")
