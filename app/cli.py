from __future__ import annotations

from pathlib import Path

import typer

from app.config import get_settings
from app.embeddings import OpenAIEmbeddingClient
from app.llm import OpenAIAnswerGenerator
from app.logging_utils import configure_logging
from app.rag_pipeline import RagPipeline

app = typer.Typer(help="CLI for the RAG policy assistant.")


def _build_pipeline() -> RagPipeline:
    settings = get_settings()
    configure_logging(settings.log_level)
    if not settings.openai_api_key:
        raise typer.BadParameter("OPENAI_API_KEY must be set in the environment or .env")

    embedding_client = OpenAIEmbeddingClient(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
    )
    answer_generator = OpenAIAnswerGenerator(
        api_key=settings.openai_api_key,
        model=settings.chat_model,
    )
    return RagPipeline(
        settings=settings,
        embedding_client=embedding_client,
        answer_generator=answer_generator,
    )


@app.command("index")
def index_command(
    docs_dir: Path | None = typer.Option(default=None, help="Directory containing .txt/.md files."),
    chunk_size: int | None = typer.Option(default=None, help="Override chunk size for indexing."),
    chunk_overlap: int | None = typer.Option(default=None, help="Override chunk overlap for indexing."),
) -> None:
    pipeline = _build_pipeline()
    result = pipeline.index_documents(
        docs_dir=docs_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    typer.echo(
        f"Indexed {result.indexed_chunks} chunks from {result.documents_indexed} documents "
        f"into index '{result.index_name}' with chunk_size={result.chunk_size} "
        f"and chunk_overlap={result.chunk_overlap}."
    )


@app.command("ask")
def ask_command(
    question: str = typer.Argument(..., help="Question to ask about the indexed documents."),
    top_k: int | None = typer.Option(default=None, help="Number of chunks to retrieve."),
) -> None:
    pipeline = _build_pipeline()
    response = pipeline.ask(question=question, top_k=top_k)
    typer.echo(response.answer)
    typer.echo(f"Grounded: {response.grounding.grounded}")
    if response.grounding.warnings:
        typer.echo("Warnings: " + ", ".join(response.grounding.warnings))
    if response.citations:
        typer.echo("Citations: " + ", ".join(response.citations))


@app.command("inspect")
def inspect_command(
    question: str = typer.Argument(..., help="Question to inspect retrieval for."),
    top_k: int | None = typer.Option(default=None, help="Number of chunks to retrieve."),
) -> None:
    pipeline = _build_pipeline()
    response = pipeline.ask(question=question, top_k=top_k)
    typer.echo(f"Grounded: {response.grounding.grounded}")
    typer.echo(f"Warnings: {', '.join(response.grounding.warnings) or 'none'}")
    typer.echo(
        f"Top score: {response.grounding.top_score:.3f} | "
        f"Average score: {response.grounding.average_score:.3f}"
    )
    for chunk in response.chunks:
        typer.echo(
            f"{chunk.citation} score={chunk.score:.3f} overlap={chunk.lexical_overlap:.3f} "
            f"source_path={chunk.source_path}"
        )
        typer.echo(chunk.text)
        typer.echo("")


if __name__ == "__main__":
    app()
