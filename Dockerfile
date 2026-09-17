# syntax=docker/dockerfile:1

FROM python:3.12.14-slim

# --- Build-time arguments ---
# DEVICE selects which uv extra to install (gpu or cpu) - see pyproject.toml
# VERSION is read from pyproject.toml by build_image.py and passed in here,
# so it never has to be typed twice.
ARG DEVICE=cpu
ARG VERSION=0.0.0

# Bake the version into the image itself, not just the tag, so a running
# container can always be traced back to the exact code it was built from.
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${VERSION}"

# --- Install uv ---
# Pinned to an exact version (never :latest) so every build - today or a year
# from now - copies the identical uv binary. Docker also caches this layer,
# so rebuilding the same Dockerfile repeatedly does NOT re-pull it each time;
# it's only re-fetched if this line changes or the build cache is cleared
# (docker build --no-cache).
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /usr/local/bin/

WORKDIR /app

# --- OS-level build tools some Python packages may need at install time ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Copy only dependency manifests first (maximizes Docker layer caching) ---
# As long as pyproject.toml/uv.lock don't change, this whole layer is reused
# on subsequent builds - only code changes below trigger a fast re-sync,
# not a full dependency reinstall.
COPY pyproject.toml uv.lock ./

# --- Install dependencies exactly as locked, for the selected device variant ---
# --frozen: fail loudly if uv.lock is out of sync with pyproject.toml, rather
# than silently re-resolving to something different than what's committed.
RUN uv sync --frozen --extra ${DEVICE} --no-install-project

# --- Now copy the rest of the project (notebooks, source code, etc.) ---
COPY . .

# --- Install the project package itself ---
RUN uv sync --frozen --extra ${DEVICE}

# --- Jupyter Lab port ---
EXPOSE 8888

# --- Launch Jupyter Lab, reachable from the host browser ---
# --NotebookApp.token='' disables the token prompt for local/dev use only.
# Remove that flag (or set a real token) if this container is ever exposed
# beyond localhost.
CMD ["uv", "run", "jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--NotebookApp.token="]
