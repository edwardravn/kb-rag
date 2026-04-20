from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.config import Settings, get_settings
from app.embeddings import OpenAIEmbeddingClient
from app.llm import OpenAIAnswerGenerator
from app.logging_utils import configure_logging
from app.rag_pipeline import RagPipeline
from app.schemas import AskRequest, AskResponse, HealthResponse, IndexRequest, IndexResponse


def build_pipeline(settings: Settings) -> RagPipeline:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required to build the default pipeline")

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


def create_app(settings: Settings | None = None, pipeline: RagPipeline | None = None) -> FastAPI:
    app = FastAPI(title="RAG Policy Assistant", version="0.2.0")
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    app.state.settings = resolved_settings
    app.state.pipeline = pipeline

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post("/index", response_model=IndexResponse)
    def index_documents(request: IndexRequest) -> IndexResponse:
        active_pipeline = _get_pipeline(app)
        docs_dir = Path(request.docs_dir) if request.docs_dir else None
        try:
            return active_pipeline.index_documents(
                docs_dir=docs_dir,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
            )
        except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/ask", response_model=AskResponse)
    def ask_question(request: AskRequest) -> AskResponse:
        active_pipeline = _get_pipeline(app)
        try:
            return active_pipeline.ask(question=request.question, top_k=request.top_k)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


def _get_pipeline(app: FastAPI) -> RagPipeline:
    pipeline: RagPipeline | None = app.state.pipeline
    if pipeline is None:
        pipeline = build_pipeline(app.state.settings)
        app.state.pipeline = pipeline
    return pipeline


app = create_app()
