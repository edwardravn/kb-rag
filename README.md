# RAG-based Policy Assistant for Grounded IT/Security Q&A

An end-to-end Python RAG system that answers enterprise policy questions with retrieved evidence, explicit grounding checks, and citation-backed responses.

## Project Highlights

- End-to-end ML/AI pipeline: ingestion, chunking, embeddings, vector retrieval, grounded generation, API, CLI, and evaluation tooling
- Real-world enterprise use case: IT and security policy Q&A, where incorrect answers can create operational and compliance risk
- Production-minded design: refusal behavior, retrieval transparency, config-driven thresholds, and test coverage
- Security-aware implementation: prompt-injection-aware prompting, untrusted-document handling, and explicit trust boundaries
- Clean, testable codebase: small architecture, focused modules, pytest coverage, and readable docs

## Problem Statement

Policy retrieval looks simple at first, but it is easy to get wrong in practice.

- Policy content is often spread across multiple markdown files, standards, and operating procedures.
- Semantic retrieval can find text that sounds related without actually being sufficient to answer the question.
- A generic LLM can hallucinate missing details, merge policies incorrectly, or overstate certainty.

In enterprise settings, those mistakes are not harmless. A wrong answer about password rules, incident reporting timelines, or privileged access approvals can lead to security gaps, process failures, or compliance issues.

That is why grounded answers matter: the assistant should answer from retrieved evidence, show what it used, and refuse when the evidence is too weak.

## Solution Overview

This project implements a lightweight Retrieval-Augmented Generation pipeline for local IT/security policy documents.

The system:

- loads local `.md` and `.txt` files
- chunks them with configurable size and overlap
- embeds chunks with OpenAI embeddings
- stores them in a local FAISS index
- retrieves relevant chunks for a question
- reranks results with a lightweight lexical-overlap heuristic
- checks whether the retrieved evidence is strong enough to answer
- generates a concise answer using only retrieved context
- returns citations, retrieved chunks, and grounding metadata for inspection

RAG helps by separating retrieval from generation: instead of asking the model to invent an answer from memory, the pipeline first finds likely evidence and only then allows the model to summarize that evidence.

What makes this implementation robust:

- explicit refusal behavior for weak evidence
- citation validation and fallback handling
- retrieval transparency in API and CLI outputs
- prompt instructions that treat retrieved documents as untrusted input
- straightforward architecture that is easy to inspect and discuss in interviews

## Key Features

- Grounded answers with citations
- Prompt injection resistance through untrusted-document handling
- Retrieval transparency with returned chunks, scores, and warning flags
- API and CLI interfaces for indexing and querying
- Lightweight evaluation tooling for retrieval sanity checks

## Architecture Summary

The flow is intentionally small and readable:

1. Ingest local policy files
2. Chunk and embed them
3. Store embeddings and chunk metadata locally
4. Retrieve top-k evidence for a question
5. Apply grounding heuristics
6. Generate a citation-backed answer or refuse

See [ARCHITECTURE.md](C:/Users/AD1914/Documents/Software%20Projects/GitHub/edwardravn/kb-rag/ARCHITECTURE.md) for the detailed flow, trust boundaries, and design decisions.

## Example Usage

Example question:

```text
What are the password length and MFA requirements for privileged accounts?
```

Example response:

```text
The retrieved documents indicate that workforce passwords must be at least 14 characters long, and privileged accounts must use multi-factor authentication. [password_policy.md#chunk_0]
```

Example citations:

```text
[password_policy.md#chunk_0]
```

## Demo Walkthrough

1. Index the sample documents.
2. Ask a policy question.
3. Inspect the answer, citations, and grounding metadata.
4. If the answer is refused, check the retrieval warnings and returned chunks to understand why.

### Step 1: Index Docs

```powershell
python -m app.cli index
```

### Step 2: Ask a Question

```powershell
python -m app.cli ask "When must a suspected security incident be reported?"
```

### Step 3: Interpret the Response

Look for:

- `Grounded: True` or `False`
- returned citations such as `[incident_reporting_standard.md#chunk_0]`
- warnings indicating weak evidence or narrow retrieval support

For retrieval debugging:

```powershell
python -m app.cli inspect "Who must approve privileged access?" --top-k 4
```

## Sample Output

CLI inspection output:

```text
Grounded: True
Warnings: none
Top score: 0.427 | Average score: 0.228
[privileged_access_standard.md#chunk_0] score=0.427 overlap=0.500 source_path=privileged_access_standard.md
Privileged access may only be granted when a documented business need exists and the request is approved by the system owner and the user's manager.
```

## How To Run Locally

### Install

```powershell
cd "C:\Users\AD1914\Documents\Software Projects\GitHub\edwardravn\kb-rag"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .[dev]
Copy-Item .env.example .env
```

### Set Environment Variables

Edit `.env`:

```env
OPENAI_API_KEY=your_real_key_here
```

### Index Documents

```powershell
python -m app.cli index
python -m app.cli index --docs-dir .\sample_docs --chunk-size 700 --chunk-overlap 100
```

### Run API

```powershell
python -m uvicorn app.main:app --reload
```

### Run CLI

```powershell
python -m app.cli ask "What is required for privileged accounts?"
python -m app.cli inspect "How quickly must a suspected incident be reported?" --top-k 4
```

## Example curl Requests

Health:

```powershell
curl http://127.0.0.1:8000/health
```

Index:

```powershell
curl -X POST http://127.0.0.1:8000/index -H "Content-Type: application/json" -d "{\"docs_dir\":\"sample_docs\",\"chunk_size\":800,\"chunk_overlap\":120}"
```

Ask:

```powershell
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d "{\"question\":\"Who must approve privileged access requests?\",\"top_k\":4}"
```

## Security Considerations

- Prompt injection risk: retrieved documents are treated as untrusted text, not instructions.
- Sensitive data exposure: retrieved chunks are returned for debugging, which is useful but increases exposure risk if sensitive docs are indexed.
- Missing auth: this demo has no authentication or authorization.
- Untrusted documents: local files are treated as evidence sources, not trusted control-plane inputs.

See [SECURITY.md](C:/Users/AD1914/Documents/Software%20Projects/GitHub/edwardravn/kb-rag/SECURITY.md) for the full threat model and hardening guidance.

## Limitations

- No auth or RBAC
- Local FAISS vector store only
- Basic grounding heuristics rather than a learned evaluator
- No document-level access control
- Not production hardened

## Future Improvements

- Auth and RBAC for API access
- Document-level access control before retrieval
- Better evaluation datasets and regression tracking
- Monitoring, structured telemetry, and quality dashboards
- Scalable vector database for larger corpora and multi-user workloads
