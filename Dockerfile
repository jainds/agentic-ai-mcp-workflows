FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose default ports
EXPOSE 8000 8001 8002 8005 8010 8011 8012

# Default command (can be overridden)
CMD ["python", "-m", "uvicorn", "services.customer.app:app", "--host", "0.0.0.0", "--port", "8000"]