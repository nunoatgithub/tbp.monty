"""Logging configuration for the RAG system."""

import logging
from pathlib import Path


LOG_FILE = Path(__file__).parent.parent / "rag.log"

def get_query_logger() -> logging.Logger:

    logger = logging.getLogger("rag.querying")

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        file_handler = logging.FileHandler(LOG_FILE, mode='a')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger


def enable_openai_logging():
    for logger_name in ["openai"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if not logger.handlers:
            file_handler = logging.FileHandler(LOG_FILE, mode='a')
            file_handler.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)


