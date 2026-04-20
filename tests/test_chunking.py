from app.chunking import TextChunker


def test_chunking_creates_stable_citations_and_metadata() -> None:
    chunker = TextChunker(chunk_size=40, chunk_overlap=10, max_chunk_chars=200)
    text = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima"

    chunks = chunker.chunk_text(text=text, source="policy.md", source_path="policy.md")

    assert len(chunks) >= 2
    assert chunks[0].citation == "[policy.md#chunk_0]"
    assert chunks[1].citation == "[policy.md#chunk_1]"
    assert chunks[0].source_path == "policy.md"
    assert chunks[0].chunk_index == 0
    assert chunks[0].char_end > chunks[0].char_start
    assert chunks[0].token_count > 0


def test_chunking_rejects_invalid_overlap() -> None:
    try:
        TextChunker(chunk_size=100, chunk_overlap=100, max_chunk_chars=100)
    except ValueError as exc:
        assert "chunk_overlap" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid overlap")
