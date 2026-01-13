"""Database layer for RAG system using DuckDB with VSS extension."""

from __future__ import annotations

import duckdb
from pathlib import Path
from typing import Any

from embedding_generator import EmbeddingGenerator


class EmbeddingDatabase:

    DB_DIR = Path(__file__).parent.parent / "indexes"

    def __init__(self, chunk_strategy_name: str):
        """
        Initialize database connection for a specific chunking strategy.

        Args:
            chunk_strategy_name: Name of chunking strategy (e.g., "chunks_500_overlap_50")
        """
        self.strategy_name = chunk_strategy_name
        self.db_path = self.DB_DIR / f"{chunk_strategy_name}.duckdb"
        self._connect()

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def _connect(self) -> None:
        self.connection = duckdb.connect(str(self.db_path))
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        if not self._schema_exists():
            self._create_schema()

    def _schema_exists(self) -> bool:
        """Check if the embeddings table exists."""
        result = self.connection.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'embeddings'
        """).fetchone()
        return result[0] > 0

    def _create_schema(self) -> None:
        """Create database schema atomically."""
        self.connection.execute("BEGIN TRANSACTION")
        try:
            # Create embeddings table with native FLOAT array type
            # Use (doc_id, chunk_index) as natural primary key
            self.connection.execute(f"""
                CREATE TABLE embeddings (
                    doc_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    embedding FLOAT[{EmbeddingGenerator.EMBEDDING_DIMENSIONS}] NOT NULL,
                    source_path TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(doc_id, chunk_index)
                )
            """)

            # Create indexes
            self.connection.execute("CREATE INDEX idx_doc_id ON embeddings(doc_id)")
            self.connection.execute("CREATE INDEX idx_source ON embeddings(source_path)")

            self.connection.execute("COMMIT")
        except Exception as e:
            self.connection.execute("ROLLBACK")
            raise RuntimeError(f"Failed to create database schema: {e}") from e

    def insert_chunks(
        self,
        doc_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        source_path: str,
        metadata: Optional[str] = None
    ) -> None:
        """
        Insert or replace chunks with their embeddings.

        Args:
            doc_id: Document identifier (typically filename or hash)
            chunks: List of text chunks
            embeddings: List of embedding vectors (same length as chunks)
            source_path: Original file path for the document
            metadata: Optional JSON metadata
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks and embeddings must have same length. "
                f"Got {len(chunks)} chunks and {len(embeddings)} embeddings."
            )

        self.connection.execute("BEGIN TRANSACTION")
        try:
            for chunk_index, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                # Insert into embeddings table (replace if exists)
                # DuckDB accepts Python lists directly for array columns
                # Use ON CONFLICT to specify which constraint to check
                self.connection.execute("""
                    INSERT INTO embeddings 
                    (doc_id, chunk_index, chunk_text, embedding, source_path, metadata)
                    VALUES (?, ?, ?, ?::FLOAT[1536], ?, ?)
                    ON CONFLICT (doc_id, chunk_index) 
                    DO UPDATE SET 
                        chunk_text = EXCLUDED.chunk_text,
                        embedding = EXCLUDED.embedding,
                        source_path = EXCLUDED.source_path,
                        metadata = EXCLUDED.metadata
                """, (doc_id, chunk_index, chunk_text, embedding, source_path, metadata))

            self.connection.execute("COMMIT")
        except Exception as e:
            self.connection.execute("ROLLBACK")
            raise RuntimeError(
                f"Failed to insert chunks for doc_id={doc_id}, source={source_path}: {e}"
            ) from e

    def similarity_search(
        self,
        query_embedding: List[float],
        k: int
    ) -> List[Dict[str, Any]]:
        """
        Find k most similar chunks using vector similarity with cosine distance.

        Args:
            query_embedding: Query vector
            k: Number of results to return

        Returns:
            List of dicts with keys: chunk_text, source_path, metadata, distance
        """
        # Use DuckDB's native array_cosine_distance function
        # Returns distance where 0.0 = identical vectors
        result = self.connection.execute("""
            SELECT 
                chunk_text,
                source_path,
                metadata,
                array_cosine_distance(embedding, ?::FLOAT[1536]) AS distance
            FROM embeddings
            ORDER BY distance
            LIMIT ?
        """, (query_embedding, k)).fetchall()

        results = []
        for row in result:
            results.append({
                'chunk_text': row[0],
                'source_path': row[1],
                'metadata': row[2],
                'distance': row[3]
            })

        return results

    def delete_by_source(self, source_path: str) -> None:
        """
        Delete all chunks from a document.

        Args:
            source_path: Path of the document to delete
        """
        self.connection.execute("BEGIN TRANSACTION")
        try:
            self.connection.execute(
                "DELETE FROM embeddings WHERE source_path = ?",
                (source_path,)
            )
            self.connection.execute("COMMIT")
        except Exception as e:
            self.connection.execute("ROLLBACK")
            raise RuntimeError(f"Failed to delete chunks for source={source_path}: {e}") from e

    def reindex_document(
        self,
        source_path: str,
        chunks: list[str],
        embeddings: list[list[float]],
        doc_id: str,
        metadata: str | None = None
    ) -> None:
        """
        Atomically delete old chunks and insert new ones.

        Args:
            source_path: Path of the document to reindex
            chunks: New text chunks
            embeddings: New embedding vectors
            doc_id: Document identifier
            metadata: Optional JSON metadata
        """
        self.connection.execute("BEGIN TRANSACTION")
        try:
            self.delete_by_source(source_path)
            self.insert_chunks(doc_id, chunks, embeddings, source_path, metadata)
            self.connection.execute("COMMIT")
        except Exception as e:
            self.connection.execute("ROLLBACK")
            raise RuntimeError(f"Failed to reindex document source={source_path}: {e}") from e

