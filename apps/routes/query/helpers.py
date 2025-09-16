from apps.llm.claude import ClaudeHandler
from apps.llm.gemini import GeminiHandler
from apps.llm.openai import OpenAIHandler
from apps.routes.query import logger
from apps.routes.query.dto import QueryInputModel
from apps.vector_stores.chroma_db import ChromaManager
from apps.vector_stores.pinecone import PineconeManager
from libs.enums import LLMType, VectorStoreType


def get_vector_store_object(session_data: dict):
    if session_data.get("vector_store") == VectorStoreType.CHROMA.name:
        vector_store_object = ChromaManager(
            collection_name=session_data.get("chroma_collection_name")
        )
        return vector_store_object.get_vector_store()
    else:
        vector_store_object = PineconeManager(
            index_name=session_data.get("pinecone_index_name")
        )
        return vector_store_object.get_vector_store()


def parse_openai_response(response):
    content = response.content
    response_metadata = response.response_metadata
    usage_metadata = response.usage_metadata
    return content, response_metadata, usage_metadata


def ask_llm(query_data: QueryInputModel, session_data: dict):
    logger.debug(
        f"Processing query - {query_data.user_query} - "
        f"Using LLM - {query_data.llm.name} - "
        f"Of Name - {session_data.get('name')} "
        f"With Vector Store - {session_data.get('vector_store')}"
    )

    llm_mapping = {
        LLMType.CLAUDE: ClaudeHandler,
        LLMType.GEMINI: GeminiHandler,
        LLMType.OPENAI: OpenAIHandler,
    }

    llm_class = llm_mapping.get(query_data.llm)
    logger.debug(f"Received LLM Class - {llm_class.__name__} ")
    vector_store_object = get_vector_store_object(session_data=session_data)
    llm = llm_class(vector_store=vector_store_object)
    logger.debug("Querying LLM for Response")
    response = llm.generate_response(
        user_query=query_data.user_query,
        prompt=query_data.prompt,
        use_context=query_data.use_context,
    )

    return parse_openai_response(response)


def create_conversation_object(
    name: str,
    llm: str,
    user_query: str,
    ai_response: str,
    response_metadata: dict,
    usage_metadata: dict,
):
    logger.debug(f"Creating conversation object ....")
    return {
        "name": name,
        "llm": llm,
        "user_query": user_query,
        "ai_response": ai_response,
        "response_metadata": response_metadata,
        "usage_metadata": usage_metadata,
    }
