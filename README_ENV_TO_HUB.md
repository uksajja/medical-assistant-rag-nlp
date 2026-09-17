# Reproducible Python Environment Setup (uv + Docker)

A reusable template for setting up a clean, reproducible Python environment for
AI/ML projects — across Windows, Linux, WSL2, and Docker — without falling into
dependency hell.

This README documents the exact workflow used for this project, and doubles as
a template for any future project (e.g. one using TensorFlow instead of
PyTorch/llama-cpp-python).

---

## Core principles

1. **One source of truth**: `pyproject.toml` (dependencies) + `uv.lock` (exact
   pinned versions). Never hand-install packages outside these files.
2. **`uv` manages everything**: Python interpreter, virtual environment, and
   dependency resolution — no conda, no manual `venv`/`pip` juggling.
3. **GPU/CPU are explicit build-time choices**, not something left to chance or
   silently inferred.
4. **The same `pyproject.toml`/`uv.lock` work on Windows, Linux, and inside
   Docker** — only *which extra* you sync changes per machine.

---

## Prerequisites (one-time, per machine)

- [`uv`](https://docs.astral.sh/uv/) installed
- For GPU work: an NVIDIA GPU + up-to-date driver. Check with:
  ```bash
  nvidia-smi
  ```
- Docker Desktop (Windows: **WSL2 backend enabled**, Settings → General)

### Avoid uv picking up a conda Python by accident

If conda is also installed, force `uv` to only ever use its own managed
Python interpreters:

```bash
uv python install 3.12
```

Add to `pyproject.toml` (see below) or set globally:
```bash
export UV_PYTHON_PREFERENCE=only-managed   # Linux/macOS
setx UV_PYTHON_PREFERENCE only-managed     # Windows (new terminal needed after)
```

---

## Step 1 — Initialize the project

```bash
uv init --python 3.12 --no-workspace
```
Creates `pyproject.toml`, `.python-version`, and a starter file.

## Step 2 — Add regular dependencies

```bash
uv add numpy pandas scikit-learn matplotlib
uv add --dev jupyter ipykernel
```
`uv add` edits `pyproject.toml`, resolves, updates `uv.lock`, and installs —
all in one step.

## Step 3 — Add GPU-capable packages with explicit CPU/GPU extras

GPU-enabled Python packages publish their CUDA builds in one of two ways —
know which one applies to your package before wiring it up:

| Package | GPU distribution method |
|---|---|
| PyTorch, llama-cpp-python | Separate **package index** per CUDA version |
| TensorFlow | Pip **extra**, e.g. `tensorflow[and-cuda]` |

### Pattern A — custom index (PyTorch / llama-cpp-python style)

```toml
[project.optional-dependencies]
gpu = ["torch", "torchvision", "llama-cpp-python"]
cpu = ["torch", "torchvision", "llama-cpp-python"]

[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[[tool.uv.index]]
name = "llamacpp-cu130"
url = "https://abetlen.github.io/llama-cpp-python/whl/cu130"
explicit = true

[[tool.uv.index]]
name = "llamacpp-cpu"
url = "https://abetlen.github.io/llama-cpp-python/whl/cpu"
explicit = true

[tool.uv.sources]
torch = [
    { index = "pytorch-cu130", extra = "gpu" },
    { index = "pytorch-cpu", extra = "cpu" },
]
torchvision = [
    { index = "pytorch-cu130", extra = "gpu" },
    { index = "pytorch-cpu", extra = "cpu" },
]
llama-cpp-python = [
    { index = "llamacpp-cu130", extra = "gpu" },
    { index = "llamacpp-cpu", extra = "cpu" },
]
```

### Pattern B — pip extra (TensorFlow style; simpler, no custom index needed)

```toml
[project.optional-dependencies]
cpu = ["tensorflow"]
gpu = ["tensorflow[and-cuda]"]
```

> **TensorFlow + native Windows**: GPU support was capped at `tensorflow<2.11`
> and was never extended further. If you need TensorFlow with GPU, do it on
> **Linux, WSL2, or Docker only** — default to the `cpu` extra on native
> Windows and any machine without a GPU.

### Either pattern — declare the extras as mutually exclusive

```toml
[tool.uv]
conflicts = [
    [
        { extra = "gpu" },
        { extra = "cpu" },
    ],
]
```

## Step 4 — Sync the environment

```bash
# GPU machine
uv sync --frozen --extra gpu

# CPU-only machine (Windows laptop, plain Linux box, etc.)
uv sync --frozen --extra cpu
```

`--frozen` makes `uv` **fail loudly** if `uv.lock` doesn't match
`pyproject.toml`, instead of silently re-resolving to something different.

## Step 5 — Verify GPU status

```bash
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# or, for TensorFlow:
uv run python -c "import tensorflow as tf; print(tf.__version__, tf.config.list_physical_devices('GPU'))"
```
An empty GPU list / `False` on a CPU-extra machine is correct, not a bug.

---

## Jupyter (VS Code or browser)

```bash
uv add --dev jupyter ipykernel
```

**Browser:**
```bash
uv run jupyter lab
```

**VS Code:** open a `.ipynb` file → **Select Kernel** → **Python Environments**
→ choose the project's `.venv` directly. (A manually registered kernel via
`ipykernel install` also works and is additionally visible from the browser,
but isn't required if you only use VS Code.)

---

## Adding a package later

```bash
uv add <package>
```
That's it — `pyproject.toml`, `uv.lock`, and `.venv` all update together.
Never delete and recreate `.venv` just to add one package.

If you ever hand-edit `pyproject.toml` directly (e.g. adding index config),
run `uv sync` afterward to apply it — hand-edits don't auto-install.

---

## Docker

### Dockerfile skeleton

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.12.14-slim

ARG DEVICE=cpu
ARG VERSION=0.0.0

LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${VERSION}"

# Pin uv to an exact version - never :latest
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /usr/local/bin/

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra ${DEVICE} --no-install-project

COPY . .
RUN uv sync --frozen --extra ${DEVICE}

EXPOSE 8888
CMD ["uv", "run", "jupyter", "lab", \
     "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", \
     "--NotebookApp.token="]
```

`.dockerignore`:
```
.venv/
__pycache__/
*.pyc
.git/
.ipynb_checkpoints/
```

### Building — always through `build_docker_image.py`, never a raw `docker build`

The project name and version are both read from `pyproject.toml` automatically
— you never type either twice, and the script is copy-pasteable into any new
project unchanged:

```bash
uv run build_docker_image.py --device cpu   # default policy for this project family
uv run build_docker_image.py --device gpu   # Linux/WSL2/Docker-with-GPU only
```

### Running — via `run_docker_image.py`, with auto-named containers

```bash
uv run run_docker_image.py --device cpu
uv run run_docker_image.py --device gpu --port 8892
```

Container names follow `<project>-<version>-<device>-<n>`, where `<n>`
auto-increments so re-running never collides with an existing (even stopped)
container name — e.g. `medical-assistant-rag-nlp-1.0.0-cpu-1`,
`-2`, `-3`, ...

---

## Pushing to Docker Hub (single private repo, multiple independent projects)

Docker Hub's free tier allows exactly **one private repository**. Since
images from completely unrelated projects all have to live in that same
repo, the project name is folded into the tag string itself — there's no
folder/category structure inside a single repo, so the tag is the only place
to encode that information.

### Tag format

```
<project-slug>-<version>-<device>
```

```
yourusername/all-projects-repo:medical-assistant-rag-nlp-1.0.0-gpu
yourusername/all-projects-repo:medical-assistant-rag-nlp-latest-cpu
yourusername/all-projects-repo:tf-image-classifier-2.0.0-gpu
yourusername/all-projects-repo:tf-image-classifier-latest-cpu
```

Project name first, then version, then device — this keeps every tag
belonging to one project sorted together alphabetically in Docker Hub's tag
list and in `docker images`, and makes the tag list searchable by project
name in Docker Hub's UI (the practical substitute for not having real
subfolders).

### One-time setup

```bash
docker login
```
In `build_docker_image.py`, set once (shared across all your projects):
```python
DOCKERHUB_USERNAME = "yourusername"
DOCKERHUB_REPO = "all-projects-repo"
```

### Build and push in one command

```bash
uv run build_docker_image.py --device gpu --push
```
This builds locally, then tags and pushes both the versioned and `latest`
tags to the shared repo automatically.

### Pulling a specific project + version later, from any machine

```bash
docker login
docker pull yourusername/all-projects-repo:medical-assistant-rag-nlp-1.0.0-gpu
```

### Keeping multi-project documentation straight

Docker Hub's repo description field can only describe one thing, so keep the
authoritative "what is this image, what tags exist, how to run it"
documentation in **each project's own git repo `README.md`** (this file),
not in Docker Hub's UI.

---

## What to commit to git

| Commit | Never commit |
|---|---|
| `pyproject.toml` | `.venv/` |
| `uv.lock` | `__pycache__/`, `*.pyc` |
| `.python-version` | Jupyter kernel registrations (machine-local) |
| `Dockerfile`, `.dockerignore` | |
| `build_docker_image.py` | |
| `run_docker_image.py` | |
| Source code / notebooks | |

**Golden rule:** `pyproject.toml` and `uv.lock` change together, in the same
commit, always. A commit with one but not the other is a broken commit.

---

## Reproducing on a new machine

```bash
git clone <repo-url>
cd <project>
uv sync --frozen --extra cpu   # or --extra gpu, per that machine's hardware
```
No manual CUDA toolkit install needed — GPU packages built with the custom-index
pattern bundle their own CUDA runtime; TensorFlow's `[and-cuda]` extra does the
same. Only the NVIDIA **driver** (and, for Docker, the NVIDIA Container
Toolkit / WSL2 GPU passthrough) needs to exist on the host.

---

## Troubleshooting quick reference

| Symptom | Cause | Fix |
|---|---|---|
| `sqlite3` DLL error in a fresh venv | `uv` picked up a conda Python | `uv python install 3.12` + `UV_PYTHON_PREFERENCE=only-managed` |
| `torch.cuda.is_available()` is `False` on a GPU machine | Got the CPU wheel from the default index | Check `tool.uv.sources` routes to the CUDA index; re-run `uv sync --frozen` |
| "No solution found... torch==X+cuY" | That exact version/build isn't published yet (very new release) | `uv pip install "torch==999" --extra-index-url <index>` to list what's actually available; pin to a real version |
| Extra-index-url in `requirements.in` seemingly ignored | `uv`'s default `first-index` strategy stops at the first index with a matching package name | Use explicit `[[tool.uv.index]]` + `tool.uv.sources` (this project's approach), not flat `--extra-index-url` lines |
| `ModuleNotFoundError` after a `langchain`-family import | Upstream package restructured/moved the module | Check the package's current docs/changelog; pin the version once fixed |
