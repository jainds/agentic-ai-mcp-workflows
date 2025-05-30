FROM python:3.11-slim

WORKDIR /app

# Install required Python packages
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    structlog \
    openai \
    anthropic \
    requests \
    python-jose \
    pydantic \
    PyJWT \
    passlib \
    bcrypt \
    python-multipart \
    httpx \
    aiohttp

# Copy the entire agents directory structure
COPY agents/ /app/agents/

# Set environment variables
ENV PYTHONPATH=/app
ENV CLAIMS_AGENT_PORT=8000

# Expose port
EXPOSE 8000

# Run the claims agent directly
CMD ["python", "agents/domain/claims_agent.py"] 