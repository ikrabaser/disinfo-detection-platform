from __future__ import annotations

import hashlib
import os
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

MODEL_ROOT = Path(
    os.getenv(
        "MODEL_ARTIFACTS_ROOT",
        str(
            BASE_DIR
            / "ml_models"
        ),
    )
)

MODEL_BUNDLE_URL = (
    os.getenv(
        "MODEL_BUNDLE_URL",
        "",
    ).strip()
)

MODEL_BUNDLE_SHA256 = (
    os.getenv(
        "MODEL_BUNDLE_SHA256",
        "",
    )
    .strip()
    .lower()
)

MODEL_ARTIFACTS_REQUIRED = (
    os.getenv(
        "MODEL_ARTIFACTS_REQUIRED",
        "false",
    )
    .strip()
    .lower()
    == "true"
)

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


class ModelArtifactError(
    RuntimeError
):
    pass


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


def missing_artifacts(
    root: Path,
) -> list[Path]:
    return [
        path
        for path in REQUIRED_FILES
        if not (
            root
            / path
        ).exists()
    ]


def artifacts_ready(
    root: Path,
) -> bool:
    return not missing_artifacts(
        root
    )


def safe_extract(
    archive_path: Path,
    destination: Path,
) -> None:
    destination = (
        destination.resolve()
    )

    with tarfile.open(
        archive_path,
        "r:gz",
    ) as archive:
        for member in (
            archive.getmembers()
        ):
            if (
                member.issym()
                or member.islnk()
            ):
                raise ModelArtifactError(
                    "Model bundle symlink "
                    "iceremez."
                )

            target = (
                destination
                / member.name
            ).resolve()

            try:
                target.relative_to(
                    destination
                )
            except ValueError as exc:
                raise ModelArtifactError(
                    "Guvenli olmayan archive "
                    f"path'i: {member.name}"
                ) from exc

        archive.extractall(
            destination
        )


def download_bundle(
    url: str,
    destination: Path,
) -> None:
    print(
        "Model bundle indiriliyor:",
        url,
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "veritas-model-provisioner/1.0"
        },
    )

    with (
        urllib.request.urlopen(
            request,
            timeout=120,
        )
        as response,
        destination.open(
            "wb"
        )
        as output,
    ):
        shutil.copyfileobj(
            response,
            output,
        )


def install_bundle(
    extracted_root: Path,
    model_root: Path,
) -> None:
    model_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    missing = (
        missing_artifacts(
            extracted_root
        )
    )

    if missing:
        formatted = "\n".join(
            f"- {path}"
            for path in missing
        )

        raise ModelArtifactError(
            "Bundle beklenen model "
            "dosyalarini icermiyor:\n"
            f"{formatted}"
        )

    for relative_path in {
        Path("berturk-mide22"),
        Path("upfd_aligned"),
        Path("bot_detection"),
    }:
        source = (
            extracted_root
            / relative_path
        )

        if not source.exists():
            continue

        destination = (
            model_root
            / relative_path
        )

        if destination.exists():
            shutil.rmtree(
                destination
            )

        shutil.move(
            str(source),
            str(destination),
        )


def provision_models() -> None:
    if artifacts_ready(
        MODEL_ROOT
    ):
        print(
            "ML model artifact'lari "
            "zaten hazir."
        )
        return

    missing = (
        missing_artifacts(
            MODEL_ROOT
        )
    )

    print(
        "Eksik model artifact sayisi:",
        len(missing),
    )

    if not MODEL_BUNDLE_URL:
        message = (
            "MODEL_BUNDLE_URL "
            "tanimli degil."
        )

        if MODEL_ARTIFACTS_REQUIRED:
            raise ModelArtifactError(
                message
            )

        print(
            "UYARI:",
            message,
        )

        print(
            "Development mode: "
            "uygulama model olmadan "
            "baslatilacak."
        )

        return

    with tempfile.TemporaryDirectory(
        prefix="veritas-models-"
    ) as temp_dir:
        temp_root = Path(
            temp_dir
        )

        archive_path = (
            temp_root
            / "models.tar.gz"
        )

        extracted_root = (
            temp_root
            / "extracted"
        )

        extracted_root.mkdir()

        download_bundle(
            MODEL_BUNDLE_URL,
            archive_path,
        )

        actual_sha256 = (
            sha256_file(
                archive_path
            )
        )

        if MODEL_BUNDLE_SHA256:
            if (
                actual_sha256
                != MODEL_BUNDLE_SHA256
            ):
                raise ModelArtifactError(
                    "Model bundle SHA256 "
                    "dogrulamasi basarisiz.\n"
                    f"Expected: "
                    f"{MODEL_BUNDLE_SHA256}\n"
                    f"Actual:   "
                    f"{actual_sha256}"
                )

        else:
            print(
                "UYARI: "
                "MODEL_BUNDLE_SHA256 "
                "tanimli degil."
            )

        safe_extract(
            archive_path,
            extracted_root,
        )

        install_bundle(
            extracted_root,
            MODEL_ROOT,
        )

    if not artifacts_ready(
        MODEL_ROOT
    ):
        raise ModelArtifactError(
            "Model provisioning sonrasi "
            "artifact dogrulamasi "
            "basarisiz."
        )

    print(
        "ML model artifact provisioning "
        "tamamlandi."
    )


def main() -> None:
    try:
        provision_models()

    except Exception as exc:
        if MODEL_ARTIFACTS_REQUIRED:
            raise

        print(
            "UYARI: Model provisioning "
            f"basarisiz: {exc}"
        )


if __name__ == "__main__":
    main()
