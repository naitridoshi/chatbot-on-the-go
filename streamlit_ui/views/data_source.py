import streamlit as st
import re

def show_data_source_options():
    st.header("Chatbot Configuration")
    chatbot_name = st.text_input("What do you want to call your chatbot?", disabled=disabled)

    st.header("Data Source")
    data_source = st.selectbox("Select a data source", ["Website", "Document", "Wikipedia"], disabled=disabled)
    
    source_input = None
    if data_source == "Website":
        url = st.text_input("Enter the website URL", disabled=disabled)
        if url and not re.match(r'^https?://', url):
            st.error("Please enter a valid URL starting with http:// or https://")
            source_input = None
        else:
            source_input = url
    elif data_source == "Document":
        st.info("Note: Only PDF, TXT, JSON, CSV, and DOCX files are allowed.")
        uploaded_files = st.file_uploader(
            "Upload up to 3 documents",
            type=["pdf", "txt", "csv", "json", "docx"],
            accept_multiple_files=True,
            disabled=disabled
        )
        if uploaded_files and len(uploaded_files) > 3:
            st.error("You can upload a maximum of 3 files.")
            source_input = None
        else:
            source_input = uploaded_files
    elif data_source == "Wikipedia":
        source_input = st.text_input("Enter the Wikipedia page name", disabled=disabled)
        
    return chatbot_name, data_source, source_input