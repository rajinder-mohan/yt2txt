FROM python:3.13-slim

# Install system dependencies including ca-certificates for proxy certificates
RUN apt-get update && apt-get install -y \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy certificate files if they exist (for Bright Data or similar proxy services)
# Create certs directory and copy certificate
COPY certs/brightdata-33335.crt /usr/local/share/ca-certificates/brightdata-33335.crt 2>/dev/null || true

# Update CA certificates (only if cert file exists)
RUN if [ -f /usr/local/share/ca-certificates/brightdata-33335.crt ]; then \
        update-ca-certificates; \
    fi

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create static directory if it doesn't exist
RUN mkdir -p static

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

