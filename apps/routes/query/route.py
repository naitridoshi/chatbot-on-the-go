from fastapi import APIRouter
from starlette.responses import JSONResponse

from apps.routes.query import logger
from apps.routes.query.dto import QueryInputModel
from apps.routes.query.helpers import ask_llm, create_conversation_object
from libs.db.mongodb.helpers import get_sessions, store_conversations
from libs.enums import Status

query_route = APIRouter(tags=["QUERY"])


@query_route.post("/query")
def query_llm(query_data: QueryInputModel):
    try:
        logger.info("Query Route accessed ...")
        session_data = get_sessions(name=query_data.name)

        if session_data is None:
            logger.error(f"Session Data Not Found - name - {query_data.name}")
            return JSONResponse(
                content={
                    "success": False,
                    "user_query": query_data.user_query,
                    "error": "Session Data Not Found.",
                },
                status_code=400,
            )

        if session_data.get("status") != Status.READY.value:
            logger.error(f"Session not ready for querying - name - {query_data.name} - status - {session_data.get('status')}")
            return JSONResponse(
                content={
                    "success": False,
                    "user_query": query_data.user_query,
                    "error": f"Session is not ready for querying. Current status: {session_data.get('status')}",
                },
                status_code=400,
            )

        logger.debug(f"Session '{query_data.name}' is ready. Proceeding with query.")

        content, response_metadata, usage_metadata = ask_llm(
            query_data=query_data, session_data=session_data
        )

        conversation_object = create_conversation_object(
            name=query_data.name,
            llm=query_data.llm.name,
            user_query=query_data.user_query,
            ai_response=content,
            response_metadata=response_metadata,
            usage_metadata=usage_metadata,
        )

        store_conversations(conversation_object)
        logger.info(f"Received Response - {str(content)}")
        return JSONResponse(
            content={
                "success": True,
                "user_query": query_data.user_query,
                "ai_response": content,
                "response_metadata": response_metadata,
                "usage_metadata": usage_metadata,
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error Occurred -  {str(e)}")
        return JSONResponse(
            content={
                "success": False,
                "query": query_data.user_query,
                "response": None,
                "error": str(e),
            },
            status_code=500,
        )
