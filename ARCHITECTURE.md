# Architecture

This project is intentionally small: it demonstrates a complete RAG pipeline without hiding the important decisions behind unnecessary abstraction.

## System Flow

```text
Local .md/.txt docs
        |
        v
  Ingestion + Normalization
        |
        v
Chunking + Metadata Creation
        |
        v
OpenAI Embeddings
        |
        v
Local FAISS Index + Metadata JSON
        |
        v
Question Embedding
        |
        v
Top-k Retrieval + Lightweight Reranking
        |
        v
Grounding Checks
   |             |
   | strong      | weak
   v             v
LLM Answer     Refusal Response
   |
   v
Citations + Retrieved Chunks + Warnings
```

## Pipeline Stages

### 1. Ingestion

- Walk a local folder
- Accept only `.md` and `.txt`
- Load documents as untrusted text
- Preserve source filename and relative path

### 2. Indexing

- Normalize whitespace for stable chunk boundaries
- Split text into overlapping chunks
- Attach chunk metadata:
  - source
  - source path
  - chunk id
  - citation
  - character offsets
  - token count
- Embed chunks and write them to a local FAISS index plus JSON metadata

### 3. Retrieval

- Embed the user question
- Retrieve top candidates from FAISS
- Rerank candidates with a lightweight lexical-overlap heuristic
- Return chunk scores and metadata for transparency

### 4. Generation

- Evaluate whether the retrieved evidence is strong enough
- Refuse when top-score, average-score, or overlap checks fail
- If grounded, send only retrieved evidence to the LLM
- Validate citations before returning the answer

## Trust Boundaries

```text
[User Question] ---------------------- untrusted
[Local Documents] -------------------- untrusted
[Retrieved Chunk Text] --------------- untrusted evidence
[Prompt Template / App Logic] -------- trusted application code
[OpenAI API] ------------------------- external dependency
[FAISS Index + Metadata JSON] -------- local application state
```

The core rule is simple: retrieved documents are evidence, not instructions.

## Design Decisions

- FAISS was chosen for a local, runnable portfolio project with minimal operational overhead.
- Grounding heuristics are explicit and readable rather than hidden in a black-box evaluator.
- Retrieved chunks are returned to make the system inspectable during debugging and interviews.
- Refusal behavior is intentional because policy QA is safer when the assistant declines weakly supported answers.

## Why The Assistant Refuses Weakly Grounded Answers

The system is designed to avoid confident failure modes. For enterprise policy questions, an incomplete or fabricated answer can be worse than no answer. The refusal path makes that trade-off explicit and observable.

For the broader threat model and security posture, see [SECURITY.md](C:/Users/AD1914/Documents/Software%20Projects/GitHub/edwardravn/kb-rag/SECURITY.md).
