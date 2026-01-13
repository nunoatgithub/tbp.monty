from __future__ import annotations

import logging
from typing import Dict, Any, List

from openai import OpenAI

from embedding_database import EmbeddingDatabase
from embedding_generator import EmbeddingGenerator
from logs import get_query_logger, enable_openai_logging


class QueryOrchestrator:

    def __init__(
        self,
        api_key: str,
        query_embedder: EmbeddingGenerator,
        embedding_db: EmbeddingDatabase
    ):
        self.query_embedder = query_embedder
        self.prompt_builder = PromptBuilder()
        self.embedding_db = embedding_db
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"
        self.logger = get_query_logger()
        enable_openai_logging()


    def query(self, question: str) -> Dict[str, Any]:
        self.logger.info("Query started: %s", question)

        context_chunks = self._retrieve_context(question)

        if not context_chunks:
            return {
                'answer': "I couldn't find relevant information in the documentation to answer your question.",
                'sources': [],
                'context_chunks': []
            }

        messages = self.prompt_builder.build_prompt(question, context_chunks)

        self.logger.info("Calling LLM model=%s with messages=%s", self.model, str(messages))
        answer = self._llm_answer(messages)

        sources = self._extract_sources(context_chunks)

        return {
            'answer': answer,
            'sources': sources,
            'context_chunks': context_chunks
        }

    @staticmethod
    def _extract_sources(context_chunks: List[Dict[str, Any]]) -> List[str]:

        sources = []
        seen = set()

        for chunk in context_chunks:
            source = chunk['source_path']
            if source not in seen:
                sources.append(source)
                seen.add(source)

        return sources

    def _retrieve_context(self, query: str) -> List[Dict[str, Any]]:
        self.logger.info("Generating embedding for query")
        query_embedding = self.query_embedder.embed_query(query)

        self.logger.info("Performing similarity search")
        results = self.embedding_db.similarity_search(query_embedding, k=5)

        if self.logger.isEnabledFor(logging.INFO):
            chunks_info = [
                {"chunk": i, "source": chunk['source_path'], "distance": chunk['distance'], "text": chunk['chunk_text'][:200]}
                for i, chunk in enumerate(results, 1)
            ]
            self.logger.info("Retrieved chunks: %s", chunks_info)

        return results

    def _llm_answer(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=messages,
                temperature=0
            )

            self.logger.debug("Raw LLM response: %s", response)

            return response.output[0].content[0].text

        except Exception as e:
            raise RuntimeError(f"Failed to generate LLM response: {e}") from e


class PromptBuilder:
    """
    Builds prompts for the LLM from retrieved context and user question.
    """

    _SYSTEM_PROMPT = """You are a helpful assistant answering questions about the Monty project documentation.

    Guidelines:
    - Only use information from the provided context
    - Cite source files when answering
    - If the context doesn't contain enough information, admit it
    - Be concise and accurate
    """

    def build_prompt(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Build chat messages for the LLM.

        Args:
            query: User's question
            context_chunks: Retrieved context chunks with metadata

        Returns:
            List of message dicts with 'role' and 'content'
        """
        # Format context
        context_text = self._format_context(context_chunks)

        # Build user message
        user_message = f"""Context from documentation:

{context_text}

Question: {query}

Please answer the question based only on the context provided above. Cite the source files when relevant."""

        # Build messages
        messages = [
            {"role": "system", "content": self._SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        return messages

    def _format_context(self, context_chunks: list[dict[str, Any]]) -> str:
        """
        Format context chunks into readable text.

        Args:
            context_chunks: List of chunks with metadata

        Returns:
            Formatted context string
        """
        formatted_chunks = []

        for i, chunk in enumerate(context_chunks, 1):
            source = chunk['source_path']
            text = chunk['chunk_text']

            formatted_chunk = f"""--- Chunk {i} (from {source}) ---
{text}
"""
            formatted_chunks.append(formatted_chunk)

        return "\n".join(formatted_chunks)