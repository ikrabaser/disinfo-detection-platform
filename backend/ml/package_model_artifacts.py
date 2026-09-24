from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

MODEL_ROOT = (
    BASE_DIR
    / "ml_models"
)

DEFAULT_OUTPUT_DIR = (
    BASE_DIR
    / "training_outputs"
    / "model_artifacts"
)

MODEL_PATHS = [
    Path("berturk-mide22"),
    Path(
        "upfd_aligned/"
        "politifact/"
        "seed_1/"
        "gcn"
    ),
    Path(
        "bot_detection/"
        "cresci_subset"
    ),
]

REQUIRED_FILES = [
    Path(
        "berturk-mide22/"
        "config.json"
    ),
    Path(
        "upfd_aligned/"
        "politifact/"
        "seed_1/"
        "gcn/"
        "model.pt"
    ),
    Path(
        "bot_detection/"
        "cresci_subset/"
        "random_forest.joblib"
    ),
]


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(
            1024 * 1024
        ):
            digest.update(chunk)

    return digest.hexdigest()


def validate_models() -> None:
    missing = [
        path
        for path in REQUIRED_FILES
        if not (
            MODEL_ROOT
            / path
        ).exists()
    ]

    if missing:
        formatted = "\n".join(
            f"- {path}"
            for path in missing
        )

        raise FileNotFoundError(
            "Eksik model artifact'lari:\n"
            f"{formatted}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--version",
        default="v1",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    args = parser.parse_args()

    validate_models()

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    bundle_name = (
        f"veritas-models-"
        f"{args.version}.tar.gz"
    )

    bundle_path = (
        args.output_dir
        / bundle_name
    )

    print("=" * 72)
    print("VERITAS MODEL ARTIFACT PACKAGER")
    print("=" * 72)

    for model_path in MODEL_PATHS:
        print(
            "Including:",
            model_path,
        )

    with tarfile.open(
        bundle_path,
        "w:gz",
    ) as archive:
        for model_path in MODEL_PATHS:
            source = (
                MODEL_ROOT
                / model_path
            )

            archive.add(
                source,
                arcname=str(
                    model_path
                ),
            )

    checksum = sha256_file(
        bundle_path
    )

    checksum_path = (
        bundle_path
        .with_suffix(
            bundle_path.suffix
            + ".sha256"
        )
    )

    checksum_path.write_text(
        f"{checksum}  "
        f"{bundle_path.name}\n",
        encoding="utf-8",
    )

    manifest = {
        "version":
            args.version,

        "bundle":
            bundle_path.name,

        "sha256":
            checksum,

        "required_files": [
            str(path)
            for path
            in REQUIRED_FILES
        ],
    }

    manifest_path = (
        args.output_dir
        / (
            f"veritas-models-"
            f"{args.version}.json"
        )
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Bundle:",
        bundle_path,
    )

    print(
        "SHA256:",
        checksum,
    )

    print(
        "Manifest:",
        manifest_path,
    )


if __name__ == "__main__":
    main()
