#!/usr/bin/env python3
"""
Build the Docker image, tagged with the version from pyproject.toml.

Edit the version in pyproject.toml by hand whenever you want to bump it.
This script just reads it and makes sure the image tag always matches.

Usage:
    uv run build_image.py
    uv run build_image.py --device cpu
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PYPROJECT = Path("pyproject.toml")
DOCKERHUB_USERNAME = "uksajja"       # <-- set this once
DOCKERHUB_REPO = "uks-docker-repo"   # <-- your single private repo name on docker hub


def get_project_field(field: str) -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(rf'^{field} = "(.*)"', text, flags=re.MULTILINE)
    if not match:
        sys.exit(f"Could not find a `{field} = \"...\"` line in {PYPROJECT}")
    return match.group(1)


def get_version() -> str:
    return get_project_field("version")


def get_project_slug() -> str:
    # pyproject.toml project names are already hyphenated/lowercase by convention
    return get_project_field("name")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Docker image tagged with pyproject.toml's version.")
    parser.add_argument("--device", choices=["gpu", "cpu"], default="gpu",
                         help="Which build variant to build (default: gpu)")
    parser.add_argument("--push", action="store_true",
                         help="Also tag and push to Docker Hub (yourusername/...)")
    args = parser.parse_args()

    version = get_version()
    project = get_project_slug()
    image_versioned = f"{project}:{version}-{args.device}"
    image_latest = f"{project}:latest-{args.device}"

    cmd = [
        "docker", "build",
        "--build-arg", f"VERSION={version}",
        "--build-arg", f"DEVICE={args.device}",
        "-t", image_versioned,
        "-t", image_latest,
        ".",
    ]
    print(f"Building version {version} ({args.device})...")
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    print(f"\nBuilt: {image_versioned}  (also tagged {image_latest})")

    if args.push:
        remote_versioned = f"{DOCKERHUB_USERNAME}/{DOCKERHUB_REPO}:{project}-{version}-{args.device}"
        remote_latest = f"{DOCKERHUB_USERNAME}/{DOCKERHUB_REPO}:{project}-latest-{args.device}"
        for local, remote in [(image_versioned, remote_versioned), (image_latest, remote_latest)]:
            run(["docker", "tag", local, remote])
            run(["docker", "push", remote])
        print(f"\nPushed: {remote_versioned}  and  {remote_latest}")


if __name__ == "__main__":
    main()
