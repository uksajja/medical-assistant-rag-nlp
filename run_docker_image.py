#!/usr/bin/env python3
"""
Run the Docker image, naming the container <image>-<version>-<device>-<n>,
where <n> auto-increments so repeated runs never collide with an existing
(stopped or running) container name.

Usage:
    uv run run_docker_image.py
    uv run run_docker_image.py --device gpu
    uv run run_docker_image.py --device cpu --port 8892
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PYPROJECT = Path("pyproject.toml")
IMAGE_NAME = "medical-assistant-rag-nlp"


def get_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version = "(.*)"', text, flags=re.MULTILINE)
    if not match:
        sys.exit(f"Could not find a `version = \"...\"` line in {PYPROJECT}")
    return match.group(1)


def next_container_name(base_name: str) -> str:
    """Find existing containers matching base_name-N and return base_name-(max+1)."""
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=True,
    )
    existing = result.stdout.splitlines()
    pattern = re.compile(rf"^{re.escape(base_name)}-(\d+)$")
    numbers = [int(m.group(1)) for name in existing if (m := pattern.match(name))]
    n = max(numbers, default=0) + 1
    return f"{base_name}-{n}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Docker image with an auto-named container.")
    parser.add_argument("--device", choices=["gpu", "cpu"], default="cpu",
                         help="Which built variant to run (default: cpu)")
    parser.add_argument("--port", default="8888", help="Host port to map to the container's 8888 (default: 8888)")
    args = parser.parse_args()

    version = get_version()
    image = f"{IMAGE_NAME}:{version}-{args.device}"
    base_name = f"{IMAGE_NAME}-{version}-{args.device}"
    container_name = next_container_name(base_name)

    cmd = ["docker", "run", "--name", container_name, "-p", f"{args.port}:8888", "-v", f"{Path.cwd()}:/app"]
    if args.device == "gpu":
        cmd += ["--gpus", "all"]
    cmd += [image]

    print(f"Running: {container_name}  (image: {image})")
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
