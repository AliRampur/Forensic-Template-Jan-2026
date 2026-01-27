# Use official Python lightweight image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Copy entrypoint script
COPY cloud-run-entrypoint.sh .
RUN chmod +x cloud-run-entrypoint.sh

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Cloud Run requires 8080)
EXPOSE 8080

# Set PORT environment variable
ENV PORT=8080

# Run entrypoint script
ENTRYPOINT ["./cloud-run-entrypoint.sh"]
