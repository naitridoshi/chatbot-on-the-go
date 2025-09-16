import streamlit as st
import sys
from pathlib import Path
import subprocess
import atexit
import time

# Add base directory to path
BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from libs.config import HOST, PORT
from streamlit_ui.views.data_source import show_data_source_options
from streamlit_ui.logic.chatbot import (
    create_chatbot_from_website,
    create_chatbot_from_document,
    create_chatbot_from_wikipedia,
)


def create_chatbot_page():
    st.set_page_config(page_title="Create Chatbot", page_icon="➕")
    st.title("Create a New Chatbot")
    st.write("This app allows you to create a chatbot from a website, a document, or a Wikipedia page.")

    # Show UI elements
    chatbot_name, data_source, source_input = show_data_source_options()

    # Button to trigger chatbot creation
    if st.button("Create Chatbot"):
        if not chatbot_name:
            st.error("Please provide a name for your chatbot.")
        else:
            with st.spinner(f"Creating chatbot '{chatbot_name}'..."):
                collection_name = None
                if data_source == "Website" and source_input:
                    collection_name = create_chatbot_from_website(source_input, chatbot_name)
                elif data_source == "Document" and source_input:
                    collection_name = create_chatbot_from_document(source_input, chatbot_name)
                elif data_source == "Wikipedia" and source_input:
                    collection_name = create_chatbot_from_wikipedia(source_input, chatbot_name)
                
                if collection_name:
                    st.session_state.collection_name = collection_name
                    st.session_state.chatbot_name = chatbot_name
                    st.session_state.messages = []
                    st.success(f"Chatbot '{chatbot_name}' created successfully!")
                    time.sleep(1)
                    st.switch_page("pages/1_💬_Chat.py")
                else:
                    st.error("Please provide the required input for the selected data source.")

if __name__ == "__main__":
    create_chatbot_page()