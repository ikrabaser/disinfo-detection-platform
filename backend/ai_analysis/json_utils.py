from __future__ import annotations

import json


def parse_json_object(
    text: str,
) -> dict:
    normalized = text.strip()

    if normalized.startswith("```"):
        lines = normalized.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip()
            == "```"
        ):
            lines = lines[:-1]

        normalized = "\n".join(
            lines
        ).strip()

    start = normalized.find("{")
    end = normalized.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "LLM yanitinda JSON object "
            "bulunamadi."
        )

    payload = json.loads(
        normalized[start:end + 1]
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "LLM yaniti JSON object olmali."
        )

    return payload
