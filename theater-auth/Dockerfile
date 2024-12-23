FROM python:3.12-slim-bookworm

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the application dependencies.
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="./src"

# Copy dependencies into the container.
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --frozen --no-cache

# Copy the application into the container.
COPY ./src .
COPY ./keys ./keys
COPY ./entrypoint.sh .

# Run the application.
ENTRYPOINT ["bash", "entrypoint.sh"]
