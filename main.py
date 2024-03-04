import streamlit as st

def create_new_form():
    with st.form("myform", clear_on_submit=True):
        x = st.text_input("Foo", key="foo")
        submit = st.form_submit_button(label="Submit")

    if submit:
        st.write("Submitted")
        st.write(x)

create_new_form()
