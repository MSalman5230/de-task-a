FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY artifacts/ ./artifacts/

# Expose the port the app runs on
EXPOSE 8000

# Run the application with gunicorn and uvicorn workers
CMD ["gunicorn", "api.app:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]