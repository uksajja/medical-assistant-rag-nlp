# v1.0.0 — Medical-Assistant-RAG-NLP

- Generative AI
- Natural Language Processing
- RAG

## Skills & Tools

- Chunking
- Embedding
- Vector Database
- Prompt Engineering
- LLMs
- Retrieval Augmented Generation (RAG)
- HyperParameter Tuning
- Response Evaluation

- tiktoken
- chromadb
- SentenceTransformers
- llama
- huggingface
- langchain

- docker

## Steps to Run the project:

- git clone [<your-repo>](https://github.com/uksajja/medical-assistant-rag-nlp.git)
- cd medical-assistant-rag-nlp

## GPU machine

- uv sync --frozen --extra gpu

## CPU-only machine (Windows laptop, plain Linux box, etc.)

- uv sync --frozen --extra cpu

## Verify GPU status

- uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"

- or for TensorFlow:

- uv run python -c "import tensorflow as tf; print(tf.__version__, tf.config.list_physical_devices('GPU'))"

- or
- uv run python verify_env.py

## Jupyter (VS Code or browser)

- uv add --dev jupyter ipykernel

## To run a python notebook in VScode

- uv run python -m ipykernel install --user --name medical-assistant-rag-nlp --display-name "Python (medical-assistant-rag-nlp)"

- VS Code: open a .ipynb file → Select Kernel → Python Environments → choose the project's .venv directly. (A manually registered kernel via ipykernel install also works and is additionally visible from the browser, but isn't required if you only use VS Code.)

## Adding a package later

- uv add <package>
   
## Docker - Build Image

### GPU image

- uv run build_docker_image.py --device gpu   # Linux/WSL2/Docker-with-GPU only

### CPU image (default)

  - uv run build_docker_image.py --device cpu   # default policy for this project family

## Docker - running

### CPU

- uv run run_docker_image.py --device cpu --port 8892

//- docker run -p 8892:8888 -v ${PWD}:/app myproject:latest-cpu

### GPU (Linux host, or Windows Docker Desktop with WSL2 backend + --gpus all)

- uv run run_docker_image.py --device gpu --port 8892

//- docker run --gpus all -p 8892:8888 -v ${PWD}:/app myproject:latest-gpu