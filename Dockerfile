FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for policy server
RUN mkdir -p /app/data

# Expose ports for all services
EXPOSE 8001 8002 8003 8501

# Default command (can be overridden in Kubernetes)
CMD ["python", "-c", "print('Insurance AI PoC container ready')"] 