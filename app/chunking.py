from __future__ import annotations

from dataclasses import dataclass

from app.schemas import ChunkRecord


@dataclass(slots=True)
class TextChunker:
    chunk_size: int
    chunk_overlap: int
    max_chunk_chars: int

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be zero or greater")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.max_chunk_chars < self.chunk_size:
            raise ValueError("max_chunk_chars must be at least as large as chunk_size")

    def chunk_text(self, text: str, source: str, source_path: str) -> list[ChunkRecord]:
        normalized = " ".join(text.split())
        if not normalized:
            return []

        chunks: list[ChunkRecord] = []
        start = 0
        chunk_index = 0

        while start < len(normalized):
            end = min(start + self.chunk_size, len(normalized))

            if end < len(normalized):
                last_space = normalized.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk_text = normalized[start:end].strip()[: self.max_chunk_chars]
            if chunk_text:
                chunks.append(
                    ChunkRecord(
                        chunk_id=f"{source}#chunk_{chunk_index}",
                        source=source,
                        source_path=source_path,
                        chunk_index=chunk_index,
                        text=chunk_text,
                        citation=f"[{source}#chunk_{chunk_index}]",
                        char_start=start,
                        char_end=start + len(chunk_text),
                        token_count=len(chunk_text.split()),
                    )
                )
                chunk_index += 1

            if end >= len(normalized):
                break

            start = max(end - self.chunk_overlap, 0)

        return chunks
