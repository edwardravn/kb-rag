# Security

This repository is a local demo system for grounded policy retrieval and question answering. It is intentionally transparent about where the security posture is good enough for a portfolio project and where it is not production-ready.

## Threat Model

The main trust boundaries are:

- user questions
- local source documents
- retrieved chunk text
- OpenAI API calls
- locally persisted vector and metadata files

The design assumes that both user input and document content may be malicious, misleading, or sensitive.

## Prompt Injection Risks

Retrieved documents are treated as untrusted evidence, not instructions. The prompt explicitly tells the model to ignore instructions found inside documents. This helps, but it does not fully solve prompt injection. A sufficiently adversarial document can still influence the model indirectly through content selection or phrasing.

## Malicious Documents

This demo does not perform:

- file-type verification beyond extension checks
- malware scanning
- content moderation
- document provenance checks

In production, uploaded or indexed documents should be scanned, validated, access-controlled, and traceable to a trusted source.

## Sensitive Data Leakage

The assistant may expose retrieved chunk text in API responses for debugging. That is intentional for operator visibility, but it increases leakage risk if sensitive documents are indexed. Only index content you are allowed to persist locally and return to the calling client.

## Over-Retrieval

Returning too many chunks can expose more raw policy text than needed. This repository mitigates that partially by:

- limiting `top_k`
- using chunk-level citations
- keeping retrieval outputs inspectable

It does not yet implement document redaction, field-level masking, or entitlement-based filtering.

## Missing Auth And Authz

The API has no authentication, authorization, or tenant isolation. That is acceptable for a local portfolio demo and unacceptable for a production deployment.

## Secret Handling

- OpenAI credentials are read from environment variables or `.env`
- The repository should never store real keys in committed files
- The application avoids logging secrets

If a real key was ever committed, it should be revoked and rotated immediately.

## Unsafe Deserialization And Dependency Concerns

This code does not use unsafe pickle-based persistence for the vector store. Metadata is stored as JSON next to the FAISS index. That reduces some deserialization risk, but dependencies still matter:

- FAISS is a native dependency
- OpenAI and FastAPI dependencies should be pinned and regularly updated
- images, binary files, and user uploads are not supported in this baseline

## Production Hardening Requirements

To move toward production, this system would need at least:

- authentication and authorization
- document-level access control before retrieval
- managed secret storage
- request logging with redaction
- rate limiting and abuse protections
- audit logging for indexing and queries
- monitoring for retrieval quality, latency, and failures
- prompt injection red-teaming and adversarial document testing
- reproducible model and index versioning
- CI security scanning and dependency review
