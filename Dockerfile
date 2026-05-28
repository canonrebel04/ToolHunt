FROM python:3.12-slim

# Install system dependencies required for sentence-transformers, FAISS, and ONNX
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first for Docker layer caching
COPY requirements-docker.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-docker.txt

# Pre-download the sentence-transformers model during build
# so it doesn't slow down the first request at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; \
               print('Downloading BAAI/bge-m3 (ONNX)...'); \
               model = SentenceTransformer('BAAI/bge-m3', backend='onnx'); \
               print('Model downloaded successfully.')"

# Copy the rest of the application
COPY . .

# Ensure the database directory exists (for bind-mount persistence at runtime)
RUN mkdir -p /app/backend/database

# Create a non-root user and change ownership
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app

USER appuser

# Expose the port Gunicorn will listen on
EXPOSE 5000

# Use Gunicorn as the WSGI server
# -w 4: 4 worker processes
# -b 0.0.0.0:5000: bind on all interfaces, port 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
