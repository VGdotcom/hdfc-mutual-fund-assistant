# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set working directory to /app
WORKDIR /app

# Install system build dependencies required for compiling vector/embedding libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user (UID 1000 required by Hugging Face Spaces security policy)
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HOST=0.0.0.0

# Copy the entire application codebase and dataset
COPY --chown=user:user . /app

# Pre-index the Qdrant vector database during Docker build time for instant server startup
RUN python -m scripts.ingest_all --collection hdfc_funds

# Expose port 7860 (Hugging Face Spaces default port)
EXPOSE 7860

# Launch Uvicorn server bound to 0.0.0.0 and dynamic PORT
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
