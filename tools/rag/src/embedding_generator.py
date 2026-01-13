from __future__ import annotations

import time
from openai import OpenAI, RateLimitError


class EmbeddingGenerator:

    MAX_BATCH_SIZE = 100
    EMBEDDING_MODEL = "text-embedding-3-small"
    # OpenAI text-embedding-3-small produces 1536-dimensional embeddings
    EMBEDDING_DIMENSIONS = 1536

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = self.EMBEDDING_MODEL

    def embed_query(self, query: str) -> List[float]:

        if not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[query]
            )

            return response.data[0].embedding

        except Exception as e:
            raise RuntimeError(f"Failed to embed query: {e}") from e

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i:i + self.MAX_BATCH_SIZE]
            batch_embeddings = self._embed_batch_with_retry(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def _embed_batch_with_retry(
        self,
        texts: list[str],
        max_retries: int = 3,
        initial_wait: float = 1.0
    ) -> list[list[float]]:

        for attempt in range(max_retries + 1):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )

                # Extract embeddings in order
                embeddings = [item.embedding for item in response.data]
                return embeddings

            except RateLimitError as e:
                if attempt < max_retries:
                    # Exponential backoff
                    delay = base_delay * (2 ** attempt)
                    print(f"Rate limit hit. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Failed to generate embeddings after {max_retries} retries: {e}"
                    ) from e

            except Exception as e:
                raise RuntimeError(f"Failed to generate embeddings: {e}") from e

        return []

