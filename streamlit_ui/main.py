__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st

def landing_page():
    st.set_page_config(page_title="Welcome to Chatbot on the Go", page_icon="👋")

    st.title("Welcome to Chatbot on the Go! 🚀")

    st.header("Your Personal AI Chatbot Builder")
    st.write(
        "This project empowers you to create your own custom AI chatbots from various data sources like websites, documents, and more. "
        "Build a chatbot that knows your data and can answer questions about it. "
        "This is a demonstration of the powerful capabilities of Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs)."
    )

    st.divider()

    st.header("About the Creator")
    st.write(
        """
        **Name:** Naitri Doshi
        **Title:** AI Expert
        
        I am passionate about building intelligent and engaging conversational AI experiences. 
        This project is a showcase of what's possible with modern AI technologies.
        """
    )

    st.divider()

    st.header("Need a Professional Chatbot for Your Business?")
    st.write(
        "The chatbot you can create here is for demonstration purposes. "
        "If you need a production-ready, real-time chatbot for your website, social media platforms (like WhatsApp, Messenger), or internal knowledge base, I can help!"
    )
    st.write("**Services include:**")
    st.markdown(
        """
        - 💬 Custom chatbot development and integration.
        - 🌐 Website and social media chatbots.
        - 🧠 Internal knowledge base and support bots.
        - 🚀 Deployment and maintenance.
        """
    )
    st.write("**Contact me at:** [naitridoshi.work@gmail.com](mailto:naitridoshi.work@gmail.com)")

    st.divider()

    if st.button("Create Your Own Demo Chatbot", type="primary", use_container_width=True):
        st.switch_page("pages/1_➕_Create_Chatbot.py")

if __name__ == "__main__":
    landing_page()