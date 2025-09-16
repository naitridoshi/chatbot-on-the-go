from fastapi import APIRouter
from starlette.responses import JSONResponse

from apps.routes.crawl.helpers import crawl_website
from apps.routes.crawl.dto import CrawlerInputModel
from apps.routes.train import logger
from libs.db.mongodb.helpers import update_session
from libs.enums import Status

crawl_route = APIRouter(tags=["CRAWLER"])


@crawl_route.post("/crawl")
async def crawl_and_store(crawl_data: CrawlerInputModel):
    try:
        logger.info(f"Crawl Route accessed for website: {crawl_data.website}")

        logger.info(f"Updating session '{crawl_data.name}' to status: {Status.CRAWLING.value}")
        update_session(name=crawl_data.name, document_to_update={
            "status": Status.CRAWLING.value,
            "name": crawl_data.name,
            "website": str(crawl_data.website)
        })

        directory_path = await crawl_website(base_url=str(crawl_data.website))
        logger.info(f"Crawling finished. Data saved to: {directory_path}")

        logger.info(f"Updating session '{crawl_data.name}' to status: {Status.CRAWLED.value}")
        update_session(name=crawl_data.name, document_to_update={
            "status": Status.CRAWLED.value,
            "source_directory": directory_path
        })

        return JSONResponse(
            content={
                "success": True,
                "message": f"Website crawled successfully. Scraped data saved to {directory_path}",
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error Occurred during crawl for session {crawl_data.name} - {str(e)}")
        logger.info(f"Updating session '{crawl_data.name}' to status: {Status.CRAWLING_FAILED.value}")
        update_session(name=crawl_data.name, document_to_update={
            "status": Status.CRAWLING_FAILED.value,
            "error": str(e)
        })
        return JSONResponse(
            content={"success": False, "error": str(e)}, status_code=500
        )