"""Unit tests for TextChunker class."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from indexing import TextChunker


class BaseTextChunkerTest:
    """Base test class providing test DSL for chunking tests."""

    @staticmethod
    def assert_chunks_match(chunk_size, chunk_overlap, text, expected_chunks):

        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        actual_chunks = chunker.chunk_text(text)

        assert len(actual_chunks) == len(expected_chunks), (
            f"Expected {len(expected_chunks)} chunks, got {len(actual_chunks)}"
        )

        for i, (actual, expected) in enumerate(zip(actual_chunks, expected_chunks)):
            assert actual == expected, (
                f"Chunk {i} mismatch:\n"
                f"Expected: {repr(expected)}\n"
                f"Actual:   {repr(actual)}"
            )


class TestTextChunkerInit(BaseTextChunkerTest):
    """Tests for TextChunker initialization."""
    def test_initializes_with_default_chunk_size_and_overlap(self):
        chunker = TextChunker()
        assert chunker.chunk_size == TextChunker.DEFAULT_CHUNK_SIZE
        assert chunker.chunk_overlap == TextChunker.DEFAULT_CHUNK_OVERLAP

    def test_initializes_with_custom_chunk_size_and_overlap(self):
        chunker = TextChunker(chunk_size=1000, chunk_overlap=100)
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 100

    def test_raises_value_error_for_invalid_chunk_size(self):
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            TextChunker(chunk_size=0)

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            TextChunker(chunk_size=-100)

    def test_raises_value_error_for_negative_overlap(self):
        with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
            TextChunker(chunk_overlap=-10)

    def test_raises_value_error_when_overlap_greater_than_or_equal_to_chunk_size(self):
        with pytest.raises(ValueError, match="chunk_overlap.*must be less than chunk_size"):
            TextChunker(chunk_size=100, chunk_overlap=100)

        with pytest.raises(ValueError, match="chunk_overlap.*must be less than chunk_size"):
            TextChunker(chunk_size=100, chunk_overlap=150)


class TestTextChunkerBasicFunctionality(BaseTextChunkerTest):
    """Tests for basic chunking functionality."""

    def test_returns_empty_list_for_empty_or_whitespace_only_text(self):
        chunker = TextChunker()
        assert chunker.chunk_text("") == []
        assert chunker.chunk_text("   ") == []
        assert chunker.chunk_text("\n\n") == []

    def test_returns_single_chunk_when_text_shorter_than_chunk_size(self):
        self.assert_chunks_match(
            chunk_size=100,
            chunk_overlap=10,
            text="This is a short text.",
            expected_chunks=["This is a short text."]
        )

    def test_returns_single_chunk_when_text_exactly_at_chunk_size(self):
        self.assert_chunks_match(
            chunk_size=20,
            chunk_overlap=0,
            text="a" * 20,
            expected_chunks=["a" * 20]
        )


class TestTextChunkerParagraphSplitting(BaseTextChunkerTest):
    """Tests for paragraph-level splitting."""

    def test_splits_text_on_paragraph_boundaries(self):
        self.assert_chunks_match(
            chunk_size=50,
            chunk_overlap=0,
            text="First paragraph.\n\nSecond paragraph.\n\nThird paragraph.",
            expected_chunks=[
                "First paragraph.\n\nSecond paragraph.\n\n",
                "Third paragraph."
            ]
        )

    def test_combines_multiple_small_paragraphs_into_one_chunk(self):
        self.assert_chunks_match(
            chunk_size=100,
            chunk_overlap=0,
            text="Para 1.\n\nPara 2.\n\nPara 3.",
            expected_chunks=["Para 1.\n\nPara 2.\n\nPara 3."]
        )


class TestTextChunkerLineSplitting(BaseTextChunkerTest):
    """Tests for line-level splitting."""

    def test_splits_text_on_line_boundaries_when_needed(self):
        self.assert_chunks_match(
            chunk_size=30,
            chunk_overlap=0,
            text="First line\nSecond line\nThird line\nFourth line",
            expected_chunks=[
                "First line\nSecond line\n",
                "Third line\nFourth line"
            ]
        )

    def test_handles_very_long_lines_exceeding_chunk_size(self):
        self.assert_chunks_match(
            chunk_size=20,
            chunk_overlap=0,
            text="This is a very long line that exceeds the chunk size significantly",
            expected_chunks=[
                "This is a very long ",
                "line that exceeds ",
                "the chunk size ",
                "significantly"
            ]
        )


class TestTextChunkerSentenceSplitting(BaseTextChunkerTest):
    """Tests for sentence-level splitting."""

    def test_splits_text_on_sentence_boundaries(self):
        self.assert_chunks_match(
            chunk_size=30,
            chunk_overlap=0,
            text="First sentence. Second sentence. Third sentence. Fourth sentence.",
            expected_chunks=[
                "First sentence. ",
                "Second sentence. ",
                "Third sentence. ",
                "Fourth sentence."
            ]
        )

    def test_keeps_sentences_together_when_possible(self):
        chunker = TextChunker(chunk_size=50, chunk_overlap=0)
        text = "Short. Another short. Yet another."
        chunks = chunker.chunk_text(text)

        assert all(chunk.strip() for chunk in chunks)


class TestTextChunkerWordSplitting(BaseTextChunkerTest):
    """Tests for word-level splitting."""

    def test_splits_text_on_word_boundaries_as_fallback(self):
        self.assert_chunks_match(
            chunk_size=20,
            chunk_overlap=0,
            text="word1 word2 word3 word4 word5 word6 word7 word8",
            expected_chunks=[
                "word1 word2 word3 ",
                "word4 word5 word6 ",
                "word7 word8"
            ]
        )


class TestTextChunkerCharacterSplitting(BaseTextChunkerTest):
    """Tests for character-level splitting (last resort)."""

    def test_splits_by_character_when_no_separators_exist(self):
        self.assert_chunks_match(
            chunk_size=10,
            chunk_overlap=0,
            text="a" * 50,
            expected_chunks=["a" * 10] * 5
        )

    def test_handles_words_longer_than_chunk_size(self):
        self.assert_chunks_match(
            chunk_size=10,
            chunk_overlap=0,
            text="supercalifragilisticexpialidocious",
            expected_chunks=[
                "supercalif",
                "ragilistic",
                "expialidoc",
                "ious"
            ]
        )


class TestTextChunkerOverlap(BaseTextChunkerTest):
    """Tests for chunk overlap functionality."""

    def test_adds_overlap_between_chunks(self):
        chunker = TextChunker(chunk_size=20, chunk_overlap=5)
        text = "This is a test sentence that will be split into multiple chunks."
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 4

        for i in range(1, len(chunks)):
            assert len(chunks[i]) > 0

    def test_chunks_without_overlap_when_overlap_is_zero(self):
        self.assert_chunks_match(
            chunk_size=20,
            chunk_overlap=0,
            text="a" * 60,
            expected_chunks=["a" * 20, "a" * 20, "a" * 20]
        )

    def test_does_not_add_overlap_to_single_chunk(self):
        self.assert_chunks_match(
            chunk_size=100,
            chunk_overlap=10,
            text="Short text",
            expected_chunks=["Short text"]
        )

    def test_calculates_overlap_correctly(self):
        chunker = TextChunker(chunk_size=30, chunk_overlap=10)
        text = "a" * 100
        chunks = chunker.chunk_text(text)

        assert len(chunks) == 5


class TestTextChunkerStrategyName(BaseTextChunkerTest):
    """Tests for strategy name generation."""

    def test_generates_strategy_name_with_default_values(self):
        chunker = TextChunker()
        name = chunker.get_chunking_strategy_name()
        assert name == f"chunks_{TextChunker.DEFAULT_CHUNK_SIZE}_overlap_{TextChunker.DEFAULT_CHUNK_OVERLAP}"

    def test_generates_strategy_name_with_custom_values(self):
        chunker = TextChunker(chunk_size=1000, chunk_overlap=100)
        name = chunker.get_chunking_strategy_name()
        assert name == "chunks_1000_overlap_100"


class TestTextChunkerEdgeCases(BaseTextChunkerTest):
    """Tests for edge cases and boundary conditions."""

    def test_returns_empty_list_for_whitespace_only_text(self):
        chunker = TextChunker()
        assert chunker.chunk_text("   \n\n   \n   ") == []

    def test_handles_text_with_multiple_types_of_separators(self):
        self.assert_chunks_match(
            chunk_size=40,
            chunk_overlap=5,
            text="Paragraph 1.\n\nLine 1\nLine 2. Sentence 1. Sentence 2.",
            expected_chunks=[
                "Paragraph 1.\n\n",
                " 1.\n\nLine 1\nLine 2. Sentence 1. Sentence 2."
            ]
        )

    def test_handles_unicode_characters_correctly(self):
        self.assert_chunks_match(
            chunk_size=50,
            chunk_overlap=10,
            text="Hello 世界! This is a test with émojis 😊 and spëcial çharacters.",
            expected_chunks=[
                "Hello 世界! This is a test with émojis 😊 and ",
                "jis 😊 and spëcial çharacters."
            ]
        )

    def test_handles_special_characters_correctly(self):
        self.assert_chunks_match(
            chunk_size=30,
            chunk_overlap=5,
            text="Test with symbols: @#$%^&*()_+-=[]{}|;:',.<>?/~`",
            expected_chunks=[
                "Test with symbols: ",
                "ols: @#$%^&*()_+-=[]{}|;:',.<>?/~`"
            ]
        )


class TestTextChunkerRealWorldScenarios(BaseTextChunkerTest):
    """Tests simulating real-world documentation scenarios."""

    def test_chunks_markdown_formatted_text_correctly(self):
        self.assert_chunks_match(
            chunk_size=100,
            chunk_overlap=20,
            text="""# Heading 1

This is a paragraph with some content.

## Heading 2

Another paragraph with more details.

- Bullet point 1
- Bullet point 2

### Heading 3

Final paragraph.""",
            expected_chunks=[
                "# Heading 1\n\nThis is a paragraph with some content.\n\n## Heading 2\n\n",
                "ent.\n\n## Heading 2\n\nAnother paragraph with more details.\n\n- Bullet point 1\n- Bullet point 2\n\n### Heading 3\n\n",
                "t 2\n\n### Heading 3\n\nFinal paragraph."
            ]
        )

    def test_chunks_text_containing_code_blocks_correctly(self):
        self.assert_chunks_match(
            chunk_size=80,
            chunk_overlap=10,
            text="""Here is some code:

```python
def example():
    return "hello"
```

And some explanation after.""",
            expected_chunks=[
                'Here is some code:\n\n```python\ndef example():\n    return "hello"\n```\n\n',
                'llo"\n```\n\nAnd some explanation after.'
            ]
        )

    def test_chunks_long_documentation_text_with_correct_overlap(self):
        self.assert_chunks_match(
            chunk_size=200,
            chunk_overlap=50,
            text="""This is a comprehensive guide to understanding the system.

The first section explains the basic concepts. It covers fundamental ideas that are essential for getting started. These concepts build upon each other progressively.

The second section dives deeper into advanced topics. Here we explore more complex scenarios and edge cases. Understanding these nuances is crucial for mastery.

Finally, the conclusion summarizes key takeaways. It reinforces the most important points and provides guidance for next steps.""",
            expected_chunks=[
                "This is a comprehensive guide to understanding the system.\n\n",
                "comprehensive guide to understanding the system.\n\nThe first section explains the basic concepts. It covers fundamental ideas that are essential for getting started. These concepts build upon each other progressively.\n\n",
                "se concepts build upon each other progressively.\n\nThe second section dives deeper into advanced topics. Here we explore more complex scenarios and edge cases. Understanding these nuances is crucial for mastery.\n\n",
                "erstanding these nuances is crucial for mastery.\n\nFinally, the conclusion summarizes key takeaways. It reinforces the most important points and provides guidance for next steps."
            ]
        )

