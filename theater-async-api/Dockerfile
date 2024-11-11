FROM python:3.11

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the application dependencies.
WORKDIR /app

# Copy the application into the container.
COPY . .

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="./src"

RUN uv sync --frozen --no-cache

# Run the application.
ENTRYPOINT ["uv", "run", "fastapi", "dev", "src/main.py", "--host", "0.0.0.0", "--port", "5000"]