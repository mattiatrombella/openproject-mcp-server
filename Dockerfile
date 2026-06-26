FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# HTTP transport listens here
EXPOSE 8000

ENV MCP_HTTP_HOST=0.0.0.0 \
    MCP_HTTP_PORT=8000 \
    PYTHONUNBUFFERED=1

CMD ["python", "openproject-mcp-http.py"]
