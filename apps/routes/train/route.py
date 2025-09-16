from pathlib import Path

from fastapi import APIRouter
from starlette.responses import JSONResponse

from apps.routes.train import logger
from apps.routes.train.dto import TrainInputModel
from apps.routes.train.helpers import load_documents, store_documents
from libs.db.mongodb.helpers import update_session, get_sessions
from libs.enums import Status, VectorStoreType

train_route = APIRouter(tags=["TRAIN"])


@train_route.post("/train")
def train_documents(train_data: TrainInputModel):
    try:
        logger.info(f"Train route accessed for session: {train_data.name}")

        document_to_update = {
            "status": Status.TRAINING.value,
            "name": train_data.name,
            "vector_store": train_data.vector_store.value,
        }
        if train_data.vector_store == VectorStoreType.CHROMA:
            document_to_update["chroma_collection_name"] = train_data.chroma_collection_name
        else:
            document_to_update["pinecone_index_name"] = train_data.pinecone_index_name

        logger.info(f"Updating session '{train_data.name}' to status: {Status.TRAINING.value}")
        update_session(name=train_data.name, document_to_update=document_to_update)

        if train_data.directory_name:
            docs_path = Path(train_data.directory_name)
            if not docs_path.exists() or not docs_path.is_dir():
                raise FileNotFoundError("Invalid Directory")
        else:
            session_data = get_sessions(name=train_data.name)
            if not session_data or "source_directory" not in session_data:
                raise ValueError("directory_name not provided and not found in session")
            docs_path = Path(session_data["source_directory"])
        
        logger.info(f"Training from directory: {docs_path}")

        documents = load_documents(train_data=train_data, directory=docs_path)
        logger.info(f"Loaded {len(documents)} document chunks.")
        store_documents(documents=documents, train_data=train_data)

        logger.info(f"Updating session '{train_data.name}' to status: {Status.READY.value}")
        update_session(name=train_data.name, document_to_update={
            "status": Status.READY.value,
            "documents": len(documents)
        })

        return JSONResponse(
            content={
                "success": True,
                "message": f"{len(documents)} chunks of documents have been stored successfully.",
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error Occurred in training session {train_data.name} - {str(e)}")
        logger.info(f"Updating session '{train_data.name}' to status: {Status.TRAINING_FAILED.value}")
        update_session(name=train_data.name, document_to_update={
            "status": Status.TRAINING_FAILED.value,
            "error": str(e)
        })
        return JSONResponse(
            content={"success": False, "error": str(e)}, status_code=500
        )
