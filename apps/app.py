import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse

BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.append(BASE_DIR)

from apps.routes.query.route import query_route
from apps.routes.train.route import train_route
from apps.routes.crawl.route import crawl_route
from libs.config import HOST, PORT, ENVIRONMENT
from libs.logger import get_logger, Colors, color_string

logger, listener = get_logger("App")
listener.start()

app = FastAPI(title="LangChain RAG API")

app.include_router(train_route)
app.include_router(query_route)
app.include_router(crawl_route)


@app.get("/")
def root():
    return JSONResponse(
        content={"success": True, "message": "Server is up and running !!!!"},
        status_code=200,
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


def start_server(
    host: str,
    port: int,
    reload: bool = True,
    workers: int = 8,
    threads: int = 10,
    environment: str = "development"
):
    if environment == "development":
        logger.info(
            color_string(
                f"Starting server on http://{host}:{port} with "
                f"{workers} workers, environment: {environment}, "
                f"reload: {reload}.",
                Colors.RED,
            ),
        )
        uvicorn.run(
            "app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="error",
            workers=workers,
        )
    elif environment == "production":
        logger.info(
            color_string(
                f"Deploying server on http://{host}:{port} with "
                f"{workers} workers, {threads} threads",
                Colors.RED,
            ),
        )
        PYTHONPATH = str(Path(__file__).resolve().parent.parent.parent.parent)
        os.environ["PYTHONPATH"] = PYTHONPATH

        command = (
            f"gunicorn "
            f"-w {workers} "
            f"--threads {threads} "
            f"-k uvicorn.workers.UvicornWorker "
            f"-b {host}:{port} app:app"
        )

        # Windows requires env vars to be set separately
        if os.name == "nt":
            # On Windows, gunicorn is not natively supported, recommend using 'uvicorn' directly
            logger.warning(
                color_string("Gunicorn is not supported on Windows. Use 'uvicorn' instead.", Colors.BOLD_RED)
            )
            command = (
                f"app:app"
                f"--host {host} --port {port} --workers {workers}"
            )

        os.system(command)
    else:
        raise ValueError(f"Invalid environment: {environment}, check env file!")



if __name__ == "__main__":
    start_server(host=HOST,
                 port=PORT,
                 environment=ENVIRONMENT)
