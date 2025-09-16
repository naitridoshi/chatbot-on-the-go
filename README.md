# Chatbot On The Go

Chatbot-on-the-go is a flexible and extensible chatbot framework that allows you to create, train, and deploy chatbots on your own data. It provides a user-friendly interface to interact with the chatbot and a powerful backend to handle data processing, LLM integration, and vector storage.

## Features

- **Multiple Data Sources:** Load data from various sources like CSV, JSON, PDF, TXT, Wikipedia, YouTube transcripts, and crawl websites.
- **Support for Multiple LLMs:** Easily switch between different Large Language Models like OpenAI's GPT, Google's Gemini, and Anthropic's Claude.
- **Vector Stores:** Utilizes vector databases like ChromaDB and Pinecone for efficient document retrieval.
- **Web Interface:** A user-friendly web interface built with Streamlit for chatbot creation and interaction.
- **REST API:** A FastAPI-based REST API for training, querying, and managing the chatbot.

## Project Structure

```
.
├── apps/                  # Core application logic
│   ├── crawlers/          # Website crawlers
│   ├── llm/               # LLM integrations (OpenAI, Gemini, Claude)
│   ├── loaders/           # Data loaders for various file formats
│   ├── routes/            # FastAPI routes for API endpoints
│   └── vector_stores/     # Vector store integrations (Chroma, Pinecone)
├── libs/                  # Shared libraries and utilities
├── streamlit_ui/          # Streamlit web interface
├── documents/             # Directory for storing scraped data
├── chroma_db/             # Directory for ChromaDB data
├── requirements.txt       # Python dependencies
└── example.env            # Example environment variables
```

## Getting Started

### Prerequisites

- Python 3.12
- Pip

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/naitridoshi/chatbot-on-the-go.git
    cd chatbot-on-the-go
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **Create a `.env` file** by copying the example file:
    ```bash
    cp example.env .env
    ```

2.  **Update the `.env` file** with your API keys and other configurations:
    ```
    PINECONE_API_KEY=""
    PINECONE_INDEX_NAME=""
    OPENAI_API_KEY=""
    CHROMA_COLLECTION_NAME="my-collection"
    CHROMA_PERSIST_DIRECTORY="chroma_db"
    OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"
    OPENAI_MODEL="gpt-3.5-turbo"
    GEMINI_MODEL="gemini-pro"
    GEMINI_API_KEY=""
    MONGO_URI="mongodb://localhost:27017/"
    DATABASE_NAME="chatbot-db"
    HOST="0.0.0.0"
    PORT="8000"
    ANTHROPIC_MODEL="claude-2"
    ANTHROPIC_API_KEY=""
    ```

## Usage

### Running the API Server

To start the FastAPI server, run the following command:

```bash
uvicorn apps.app:app --host 0.0.0.0 --port 8000 --reload
```

The API documentation will be available at `http://localhost:8000/docs`.

### Running the Streamlit UI

To start the Streamlit web interface, run the following command:

```bash
streamlit run streamlit_ui/main.py
```

The web interface will be available at `http://localhost:8501`.
