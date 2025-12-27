FROM python:3.12-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev, no virtualenv)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy application code
COPY app/ ./app/
COPY var/data/ ./var/data/

# Environment variables for paths
ENV DATA_PATH=/app/var/data
ENV IMAGES_PATH=/app/var/data/images

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
