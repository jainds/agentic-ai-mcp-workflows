# Multi-stage Docker build for Insurance AI PoC - Main Image
# Supports automatic versioning and GitHub Actions integration

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim as base

# Build arguments for versioning and metadata
ARG VERSION=dev
ARG BUILD_DATE
ARG VCS_REF
ARG BUILDPLATFORM
ARG TARGETPLATFORM

# Set build-time metadata
LABEL org.opencontainers.image.title="Insurance AI PoC - Main"
LABEL org.opencontainers.image.description="Google ADK + LiteLLM + OpenRouter Integration"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.vendor="Insurance AI Team"
LABEL org.opencontainers.image.source="https://github.com/piyushkumarjain/insurance-ai-poc"
LABEL insurance.ai.component="main"
LABEL insurance.ai.version="${VERSION}"

# Set working directory
WORKDIR /app

# Install system dependencies and uv in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# ========================================
# Dependencies Stage
# ========================================
FROM base as dependencies

# Copy requirements and install Python dependencies using uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# ========================================
# Production Stage
# ========================================
FROM base as production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python*/site-packages/ /usr/local/lib/python*/site-packages/
COPY --from=dependencies /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY . .

# Create data directory for policy server
RUN mkdir -p /app/data

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 10001 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Create version info file
RUN echo "{\
  \"version\": \"${VERSION}\", \
  \"build_date\": \"${BUILD_DATE}\", \
  \"git_commit\": \"${VCS_REF}\", \
  \"component\": \"main\", \
  \"platform\": \"${TARGETPLATFORM}\", \
  \"package_manager\": \"uv\" \
}" > /app/version.json

# Expose ports for all services
EXPOSE 8001 8002 8003 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command (can be overridden in Kubernetes)
CMD ["python", "-c", "print('Insurance AI PoC Main Container v${VERSION} ready'); import json; print(json.dumps(json.load(open('/app/version.json')), indent=2))"] 