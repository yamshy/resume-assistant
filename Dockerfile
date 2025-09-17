FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/
COPY app/ ./app/
COPY tests/ ./tests/
COPY pytest.ini .

# Install dependencies
RUN uv pip install --system -e .[dev]

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]