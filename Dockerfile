ARG PYTHON_VERSION=3.14.2

FROM python:${PYTHON_VERSION} as builder

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the application dependencies.
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

FROM python:${PYTHON_VERSION}-slim as runtime

# Copy the virtual env dependencies leaving other installed stuff on the builder.
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy the application into the container.
COPY src ./src

# Run the application.
ENTRYPOINT ["granian"]
CMD [ \
    "--interface", "asgi", \
    "src.http.app:app", \
    "--host", "0.0.0.0", \
    "--port", "8080", \
    "--loop", "uvloop", \
    "--log-level", "info" \
    ]

