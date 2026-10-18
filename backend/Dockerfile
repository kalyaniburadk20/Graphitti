FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /workspace

# Install the pinned backend dependencies.
COPY backend/requirements.txt /workspace/backend/requirements.txt

ENV PIP_DEFAULT_TIMEOUT=30
ENV PIP_RETRIES=2

RUN python -m pip install \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple \
    "torch==2.13.0+cpu" \
    && python -m pip install \
    -r /workspace/backend/requirements.txt

RUN python -m pip install --no-cache-dir python-dotenv==1.2.3
RUN python -m pip install --no-cache-dir rank-bm25
RUN python -m pip install --no-cache-dir faiss-cpu

# Copy backend source code.
COPY backend/ /workspace/backend/

# Include the committed benchmark snapshot, not local processed data.
COPY data/benchmark/ /workspace/data/benchmark/

# Create directories used by website ingestion.
RUN mkdir -p /workspace/data/raw /workspace/data/processed

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --app-dir /workspace/backend --host 0.0.0.0 --port ${PORT:-8000}"]