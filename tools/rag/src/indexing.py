from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from embedding_database import EmbeddingDatabase
from embedding_generator import EmbeddingGenerator


class IndexOrchestrator:

    def __init__(
        self,
        text_chunker: TextChunker,
        embedding_generator: EmbeddingGenerator,
        embedding_db: EmbeddingDatabase
    ):
        self.document_loader = DocumentLoader()
        self.text_chunker = text_chunker
        self.embedding_generator = embedding_generator
        self.embedding_db = embedding_db

    def index_documents(self, file_paths: list[Path] | None = None) -> dict[str, Any]:
        # Load documents
        if file_paths:
            documents = []
            for file_path in file_paths:
                try:
                    doc = self.document_loader.load_single_document(file_path)
                    documents.append(doc)
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    continue
        else:
            documents = self.document_loader.load_documents()

        # Process documents
        stats = {
            'total': len(documents),
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        print(f"Indexing {len(documents)} documents with strategy: {self.text_chunker.get_chunking_strategy_name()}")

        for file_path, content in documents:
            try:
                self._index_single_document(file_path, content)
                stats['succeeded'] += 1
                print(f"✓ Indexed: {file_path}")
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Failed to index {file_path}: {e}"
                stats['errors'].append(error_msg)
                print(f"✗ {error_msg}")
                continue

        return stats

    def reindex_file(self, file_path: Path) -> dict[str, Any]:
        try:
            file_path, content = self.document_loader.load_single_document(file_path)

            # Generate doc_id
            doc_id = self._generate_doc_id(file_path)

            # Chunk text
            chunks = self.text_chunker.chunk_text(content)
            if not chunks:
                return {
                    'succeeded': 0,
                    'failed': 1,
                    'error': f"No chunks generated from {file_path}"
                }

            # Generate embeddings
            embeddings = self.embedding_generator.embed_texts(chunks)

            # Reindex atomically
            source_path = str(file_path)
            self.embedding_db.reindex_document(
                source_path=source_path,
                chunks=chunks,
                embeddings=embeddings,
                doc_id=doc_id
            )

            print(f"✓ Reindexed: {file_path} ({len(chunks)} chunks)")

            return {
                'succeeded': 1,
                'failed': 0,
                'chunks': len(chunks)
            }

        except Exception as e:
            error_msg = f"Failed to reindex {file_path}: {e}"
            print(f"✗ {error_msg}")
            return {
                'succeeded': 0,
                'failed': 1,
                'error': error_msg
            }

    def _index_single_document(self, file_path: Path, content: str) -> None:

        doc_id = self._generate_doc_id(file_path)

        chunks = self.text_chunker.chunk_text(content)
        if not chunks:
            print(f"Warning: No chunks generated from {file_path}")
            return

        embeddings = self.embedding_generator.embed_texts(chunks)

        source_path = str(file_path)
        self.embedding_db.insert_chunks(
            doc_id=doc_id,
            chunks=chunks,
            embeddings=embeddings,
            source_path=source_path
        )

    @staticmethod
    def _generate_doc_id(file_path: Path) -> str:
        normalized_path = str(file_path.resolve())
        return hashlib.md5(normalized_path.encode()).hexdigest()


class DocumentLoader:

    def __init__(self):
        self.docs_root = Path(__file__).resolve().parents[3] / "docs"

    def load_documents(self) -> list[tuple[Path, str]]:
        documents = []
        for md_file in self.docs_root.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                documents.append((md_file, content))
            except Exception as e:
                print(f"Warning: Failed to read {md_file}: {e}")
                continue

        return documents

    @staticmethod
    def load_single_document(file_path: Path) -> tuple[Path, str]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        if not file_path.suffix == '.md':
            raise ValueError(f"Not a markdown file: {file_path}")

        content = file_path.read_text(encoding='utf-8')
        return file_path, content


class TextChunker:
    """
    Splits text into overlapping chunks using recursive splitting at semantic boundaries.
    """

    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    # Separator priority: paragraph → line → sentence → word → character
    SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP):

        if chunk_size <= 0:
            raise ValueError(
                f"chunk_size must be positive, got {chunk_size}. "
            )

        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be non-negative, got {chunk_overlap}")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def get_chunking_strategy_name(self) -> str:
        return f"chunks_{self.chunk_size}_overlap_{self.chunk_overlap}"

    def chunk_text(self, text: str) -> list[str]:

        if not text.strip():
            return []

        chunks = self._recursive_split(text, self.SEPARATORS)

        # Add overlap between chunks (only at top level, not during recursion)
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks = self._add_overlap(chunks)

        return chunks

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:

        if not separators:
            return self._split_by_size(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        if not separator:
            # Empty separator means split by character
            return self._split_by_size(text)

        splits = text.split(separator)

        # Merge splits into chunks
        chunks = []
        current_chunk = ""

        for split in splits:
            # Re-add separator except for last split
            split_with_sep = split + separator if split != splits[-1] else split

            if len(current_chunk) + len(split_with_sep) <= self.chunk_size:
                # Add to current chunk
                current_chunk += split_with_sep
            else:
                # Current chunk is full
                if current_chunk:
                    chunks.append(current_chunk)

                # Check if split itself is too large
                if len(split_with_sep) > self.chunk_size:
                    # Recursively split with next separator
                    sub_chunks = self._recursive_split(split_with_sep, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = split_with_sep

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_by_size(self, text: str) -> list[str]:

        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def _add_overlap(self, chunks: list[str]) -> list[str]:

        if not chunks or len(chunks) == 1:
            return chunks

        overlapped_chunks = [chunks[0]]

        for i in range(1, len(chunks)):
            # Get overlap from ORIGINAL previous chunk (not the overlapped one)
            original_prev_chunk = chunks[i - 1]
            overlap_text = original_prev_chunk[-self.chunk_overlap:] if len(original_prev_chunk) > self.chunk_overlap else original_prev_chunk

            # Add overlap to current chunk
            current_chunk = overlap_text + chunks[i]
            overlapped_chunks.append(current_chunk)

        return overlapped_chunks