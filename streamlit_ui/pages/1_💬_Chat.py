__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sys
from pathlib import Path

# Add base directory to path
BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from apps.vector_stores.chroma_db import ChromaManager
from apps.llm.gemini import GeminiHandler

def chat_page():
    st.set_page_config(page_title="Chat", page_icon="💬")

    if "collection_name" in st.session_state:
        chatbot_name = st.session_state.get("chatbot_name", "Chatbot")
        st.title(f"Chat with {chatbot_name}")
    else:
        st.title("Chatbot")
        st.info("Please create a chatbot from the main page first.")
        st.page_link("main.py", label="Create a new chatbot", icon="➕")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask your question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                chroma_manager = ChromaManager(collection_name=st.session_state.collection_name)
                vector_store = chroma_manager.get_vector_store()
                
                handler = GeminiHandler(vector_store=vector_store)
                response = handler.generate_response(user_query=prompt, prompt=None)
                
                response_content = response.content
                st.markdown(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})

if __name__ == "__main__":
    chat_page()