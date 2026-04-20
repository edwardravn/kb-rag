from __future__ import annotations

from pathlib import Path


def load_documents(docs_dir: Path) -> list[tuple[str, str, str]]:
    if not docs_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {docs_dir}")
    if not docs_dir.is_dir():
        raise NotADirectoryError(f"Documents path is not a directory: {docs_dir}")

    documents: list[tuple[str, str, str]] = []
    for path in sorted(docs_dir.rglob("*")):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        relative_path = str(path.relative_to(docs_dir)).replace("\\", "/")
        documents.append((path.name, relative_path, text))

    if not documents:
        raise ValueError(f"No supported .txt or .md files found in: {docs_dir}")

    return documents
