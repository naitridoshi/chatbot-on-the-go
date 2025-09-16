import streamlit as st
import asyncio
from pathlib import Path
import shutil

from apps.routes.crawl.helpers import crawl_website
from apps.routes.train.helpers import store_documents
from apps.routes.train.dto import TrainInputModel
from libs.enums import VectorStoreType
from apps.loaders.csv_loader import CSVLoader
from apps.loaders.docs_loader import DocsLoader
from apps.loaders.json_loader import JSONDocLoader
from apps.loaders.pdf_loader import PDFLoader
from apps.loaders.txt_loader import TxtLoader
from apps.loaders.wikipedia_loader import WikipediaPageLoader
from apps.loaders.youtube_transcripts_loader import YoutubeUrlLoader

def create_chatbot_from_website(url: str, name: str):
    st.write("Crawling website...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    directory = loop.run_until_complete(crawl_website(url))
    st.write("Website crawled successfully!")
    
    st.write("Training chatbot...")
    all_documents = []
    json_loader = JSONDocLoader(directory=Path(directory))
    all_documents.extend(json_loader.load_documents())
    
    train_input = TrainInputModel(
        name=name,
        vector_store=VectorStoreType.CHROMA,
        chroma_collection_name=name,
    )
    store_documents(documents=all_documents, train_data=train_input)

    if Path(directory).exists():
        shutil.rmtree(Path(directory))

    st.write("Chatbot trained successfully!")
    return train_input.chroma_collection_name

def create_chatbot_from_document(uploaded_files: list, name: str):
    st.write("Training chatbot from documents...")
    temp_dir = Path("temp") / name
    temp_dir.mkdir(exist_ok=True, parents=True)

    for uploaded_file in uploaded_files:
        file_path = temp_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    all_documents = []
    
    # Map file extensions to loader classes
    loader_map = {
        ".pdf": PDFLoader,
        ".txt": TxtLoader,
        ".csv": CSVLoader,
        ".json": JSONDocLoader,
        ".docx": DocsLoader,
    }

    for uploaded_file in uploaded_files:
        file_extension = Path(uploaded_file.name).suffix
        loader_class = loader_map.get(file_extension)
        
        if loader_class:
            loader = loader_class(directory=temp_dir)
            all_documents.extend(loader.load_documents())

    train_input = TrainInputModel(
        name=name,
        vector_store=VectorStoreType.CHROMA,
        chroma_collection_name=name,
    )
    store_documents(documents=all_documents, train_data=train_input)

    if Path("temp").exists():
        shutil.rmtree(Path("temp"))

    st.write("Chatbot trained successfully!")
    return train_input.chroma_collection_name

def create_chatbot_from_wikipedia(page_name: str, name: str):
    st.write("Training chatbot from Wikipedia...")
    loader = WikipediaPageLoader(query=page_name)
    documents = loader.load_documents()
    
    train_input = TrainInputModel(
        name=name,
        vector_store=VectorStoreType.CHROMA,
        chroma_collection_name=name,
    )
    store_documents(documents=documents, train_data=train_input)
    st.write("Chatbot trained successfully!")
    return train_input.chroma_collection_name

def create_chatbot_from_youtube(video_url: str, name: str):
    st.write("Training chatbot from YouTube...")
    loader = YoutubeUrlLoader()
    documents = loader.load_documents(youtube_links=[video_url])
    
    train_input = TrainInputModel(
        name=name,
        vector_store=VectorStoreType.CHROMA,
        chroma_collection_name=name,
    )
    store_documents(documents=documents, train_data=train_input)
    st.write("Chatbot trained successfully!")
    return train_input.chroma_collection_name
