# The python version must match the version in .python-version
FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS builder

ARG HANDLER
ENV HANDLER=${HANDLER}

# Set flags for execution environment
# These can be changes if underlying infrastructure is updated
ENV CMAKE_ARGS="-DLLAMA_NATIVE=OFF -DGGML_NATIVE=OFF -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS -DGGML_AVX512=OFF -DGGML_AVX512_VNNI=OFF -DGGML_AVX512_VBMI=OFF -DGGML_AVX512_BF16=OFF"
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONPATH=.
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --frozen --no-install-project --extra llm --no-dev --no-python-downloads
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --extra llm --no-python-downloads


# Then, use a final image without uv
FROM python:3.11-bookworm

ARG HANDLER
ENV HANDLER=${HANDLER} PYTHONPATH=.

# Copy the application from the builder
COPY --from=builder --chown=app:app /app /app
WORKDIR /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Run the service using the path to the handler
ENTRYPOINT python -u $HANDLER