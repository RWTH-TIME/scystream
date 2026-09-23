"""Checks that the Airflow and Superset versions used across the repository
fit together and prints them as GitHub step outputs.

* all docker-compose files use the same apache/airflow image
* the apache-airflow-client of core matches the Airflow major.minor version
  (the client models are generated per Airflow release and fail to validate
  responses of other minor versions)
* the Superset image used in docker-compose builds superset/Dockerfile
"""

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILES = ["docker-compose.yml", "docker-compose.dev.yml"]

errors: list[str] = []


def airflow_images() -> dict[str, str]:
    images = {}
    for name in COMPOSE_FILES:
        text = (ROOT / name).read_text()
        match = re.search(
            r"AIRFLOW_IMAGE_NAME:-(apache/airflow:[\w.\-]+)", text,
        )
        if not match:
            errors.append(f"{name}: no apache/airflow image found")
            continue
        images[name] = match.group(1)
    return images


def airflow_client_version() -> str | None:
    text = (ROOT / "core" / "requirements.txt").read_text()
    match = re.search(r"^apache-airflow-client==([\w.]+)$", text, re.M)
    if not match:
        errors.append(
            "core/requirements.txt: apache-airflow-client is not pinned",
        )
        return None
    return match.group(1)


def superset_version() -> str | None:
    text = (ROOT / "superset" / "Dockerfile").read_text()
    match = re.search(r'ARG SUPERSET_VERSION="([\w.\-]+)"', text)
    if not match:
        errors.append("superset/Dockerfile: SUPERSET_VERSION not found")
        return None
    for name in COMPOSE_FILES:
        if not re.search(r"^\s+build: superset$", (ROOT / name).read_text(),
                         re.M):
            errors.append(f"{name}: superset service must build ./superset")
    return match.group(1)


def minor(version: str) -> tuple[str, ...]:
    return tuple(version.split(".")[:2])


def main() -> int:
    images = airflow_images()
    client = airflow_client_version()
    superset = superset_version()

    if len(set(images.values())) > 1:
        errors.append(f"docker-compose files use different Airflow images: "
                      f"{images}")

    image = next(iter(images.values()), None)
    airflow_version = image.split(":", 1)[1] if image else None
    if airflow_version and client and minor(client) != minor(airflow_version):
        errors.append(
            f"apache-airflow-client {client} does not match Airflow "
            f"{airflow_version} (major.minor must be equal)"
        )

    if errors:
        print("\n".join(f"::error::{e}" for e in errors))
        return 1

    outputs = {
        "airflow_image": image,
        "airflow_version": airflow_version,
        "airflow_client_version": client,
        "superset_version": superset,
    }
    for key, value in outputs.items():
        print(f"{key}={value}")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            for key, value in outputs.items():
                f.write(f"{key}={value}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
