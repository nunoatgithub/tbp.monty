"""Main entry point for the RAG system."""

import os
import sys

from dotenv import load_dotenv

from cli import REPL
from embedding_database import EmbeddingDatabase
from embedding_generator import EmbeddingGenerator
from indexing import IndexOrchestrator
from indexing import TextChunker
from querying import QueryOrchestrator


def main():
    """Initialize components and start REPL."""

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment.")
        print("Please create a .env file with your OpenAI API key.")
        print("See .env.template for an example.")
        sys.exit(1)


    text_chunker = TextChunker()
    embedding_db = EmbeddingDatabase(text_chunker.get_chunking_strategy_name())
    embedding_generator = EmbeddingGenerator(api_key)

    index_orchestrator = IndexOrchestrator(
        text_chunker,
        embedding_generator,
        embedding_db
    )

    query_orchestrator = QueryOrchestrator(
        api_key,
        embedding_generator,
        embedding_db
    )

    repl = REPL(index_orchestrator, query_orchestrator)

    try:
        repl.run()
    finally:
        embedding_db.close()


if __name__ == "__main__":
    main()
