# Exact Python release and immutable multi-platform image digest.
FROM python:3.12.16-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

# Copy only the pinned uv executable from Astral's official image.
COPY --from=ghcr.io/astral-sh/uv:0.13.8@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85 /uv /usr/local/bin/uv

# Keep the Linux environment inside the image; use the existing base Python.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Create a fixed, unprivileged identity and its writable development paths.
RUN groupadd --gid 10001 reprolab \
    && useradd --no-log-init --uid 10001 --gid reprolab --create-home --shell /bin/sh reprolab \
    && mkdir -p /app /opt/venv /var/lib/reprolab \
    && chown reprolab:reprolab /app /opt/venv /var/lib/reprolab

WORKDIR /app

# Explicit copies plus .dockerignore keep host data/secrets/environments out.
COPY --chown=reprolab:reprolab pyproject.toml uv.lock README.md ./

USER reprolab:reprolab

# Install the existing lock, including development tools, without source builds.
# uv's temporary download cache is discarded when this instruction finishes.
RUN uv sync --locked --no-cache --no-build \
    && python --version \
    && uv --version

# S03 has no application entry point; make the default command observable.
CMD ["python", "--version"]
