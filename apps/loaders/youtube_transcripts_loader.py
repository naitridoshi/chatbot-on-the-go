from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders.youtube import TranscriptFormat

from apps.loaders import logger


class YoutubeUrlLoader:

    def __init__(self, chunk_size_seconds: int = 120):
        logger.info(
            f"Initializing Youtube Loader "
            f"Chunk Size In Seconds - {chunk_size_seconds} "
        )

        self.chunk_size_seconds = chunk_size_seconds

    def load_documents(self, youtube_links: list, add_video_info: bool = False):

        logger.debug(
            f"Loading all youtube links - "
            f"Found {len(youtube_links)} to be loaded"
        )

        all_documents = []
        for link in youtube_links:
            try:
                loader = YoutubeLoader.from_youtube_url(
                    str(link),
                    add_video_info=add_video_info,
                    transcript_format=TranscriptFormat.CHUNKS,
                    chunk_size_seconds=self.chunk_size_seconds,
                )
                all_documents.extend(loader.load())
            except Exception as e:
                logger.warning(f"Could not load transcript for {link}: {e}")
        logger.debug(f"Split loaded documents into {len(all_documents)} chunks")
        return all_documents
