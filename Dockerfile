FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md SECURITY.md ARCHITECTURE.md ./
COPY app ./app
COPY sample_docs ./sample_docs
COPY scripts ./scripts

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
