from langchain_anthropic import ChatAnthropic

from apps.llm import logger
from libs.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from libs.constants import prompt_template, system_prompt


class ClaudeHandler:

    def __init__(
        self,
        model: str = ANTHROPIC_MODEL,
        temperature: int = 0,
        top_p: float = 0.7,
        vector_store=None,
        api_key=ANTHROPIC_API_KEY,
    ):

        logger.info(f"Initializing Llm Model {model} ")

        if vector_store is None:
            logger.error("Vector Store is not provided.")
            raise Exception("Vector Store is not provided.")

        self.vector_store = vector_store
        llm = ChatAnthropic(
            model=model, temperature=temperature, top_p=top_p, api_key=api_key
        )
        self.llm = llm

    def generate_response(
        self,
        user_query: str,
        prompt: str,
        top_k: int = 3,
        use_context: bool = True,
    ):
        logger.info(
            f"Generating Response for user query - {user_query} - use_context - {use_context}"
        )

        retrieved_docs = []
        if use_context:
            results = self.vector_store.similarity_search(user_query, k=top_k)
            retrieved_docs = [doc.page_content for doc in results]

        if retrieved_docs:
            context_sections = []
            for i, doc in enumerate(retrieved_docs, 1):
                context_sections.append(f"Document {i}:\n{doc}")
            context_text = "\n\n".join(context_sections)
        else:
            context_text = "No additional context available."

        formatted_prompt = prompt_template.format(
            system_prompt=system_prompt, context=context_text, query=user_query
        )
        if prompt:
            formatted_prompt = f"{prompt}\n\n{formatted_prompt}"

        response = self.llm.invoke(formatted_prompt)
        return response
