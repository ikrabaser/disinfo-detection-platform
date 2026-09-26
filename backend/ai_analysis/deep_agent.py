from __future__ import annotations

import copy
import json
import time
from typing import Any, Callable

from agent.client import AgentRunner
from agent.prompts import (
    VERITAS_SYSTEM_PROMPT,
)
from agent.tool_schemas import (
    build_assistant_tool_definitions,
)
from llm import (
    LLMMessage,
    LLMProvider,
    LLMProviderError,
)


DEEP_TOOL_NAMES = frozenset(
    {
        "get_analysis_result",
        "search_evidence",
    }
)


DEEP_REVIEW_SYSTEM_PROMPT = (
    VERITAS_SYSTEM_PROMPT
    + """

DERIN ANALIZ REVIEW KATMANI

Bu calisma VERITAS Deep Analysis pipeline'inin
ikinci inceleme katmanidir.

Structured evidence pipeline daha once
calistirilmistir. Sana verilen sonucu nihai
gercek olarak kabul etme.

Final yanit vermeden once:

1. get_analysis_result tool'unu verilen
   analysis_id ile cagir.

2. Ana kontrol edilebilir iddia icin
   search_evidence tool'unu en az bir kez
   kullan.

3. NLP, GNN ve bot ciktilarini evidence ile
   karistirma. Bunlar yalnizca model
   sinyalleridir.

4. Cross-domain ve kalibre edilmemis skorlar
   dogruluk olasiligi degildir.

5. Evidence yetersizse INSUFFICIENT sonucunu
   koru. Boslugu model bilgisiyle doldurma.

6. Tool sonucunda bulunmayan URL, kurum,
   tarih veya kanit uydurma.

Yanit kisa ama aciklanabilir olsun.

Su basliklari kullan:

Degerlendirme
Kanit Ozeti
Model Sinyalleri
Agent Kontrolleri
Sinirlamalar
"""
).strip()


def _compact_structured_result(
    result: dict[str, Any],
) -> dict[str, Any]:
    report = result.get(
        "report"
    )

    if not isinstance(
        report,
        dict,
    ):
        return {
            "status":
                result.get("status"),
            "report": None,
        }

    raw_evidence = (
        report.get("evidence")
        or {}
    )

    compact_evidence = {}

    if isinstance(
        raw_evidence,
        dict,
    ):
        for (
            claim_id,
            items,
        ) in raw_evidence.items():

            if not isinstance(
                items,
                list,
            ):
                continue

            compact_items = []

            for item in items[:5]:
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                summary = (
                    item.get("summary")
                    or item.get("content")
                    or ""
                )

                compact_items.append(
                    {
                        "id":
                            item.get("id"),
                        "title":
                            item.get("title"),
                        "url":
                            item.get("url"),
                        "source":
                            item.get("source"),
                        "rating":
                            item.get("rating"),
                        "evidence_type":
                            item.get(
                                "evidence_type"
                            ),
                        "summary":
                            str(summary)[
                                :700
                            ],
                    }
                )

            compact_evidence[
                str(claim_id)
            ] = compact_items

    return {
        "status":
            result.get("status"),
        "provider":
            result.get("provider"),
        "model":
            result.get("model"),
        "overall_evidence_status":
            report.get(
                "overall_evidence_status"
            ),
        "claims":
            report.get("claims")
            or [],
        "assessments":
            report.get(
                "assessments"
            )
            or [],
        "manipulation_signals":
            report.get(
                "manipulation_signals"
            )
            or [],
        "evidence":
            compact_evidence,
        "retrieval_mode":
            report.get(
                "retrieval_mode"
            ),
        "limitations":
            report.get(
                "limitations"
            )
            or [],
    }


def _execute_deep_tool(
    runner: AgentRunner,
    name: str,
    arguments: dict[str, Any],
):
    result = runner.call_tool(
        name,
        **arguments,
    )

    if (
        name
        != "get_analysis_result"
        or not isinstance(
            result,
            dict,
        )
    ):
        return result

    cleaned = copy.deepcopy(
        result
    )

    ai_result = cleaned.get(
        "ai_analysis_result"
    )

    if isinstance(
        ai_result,
        dict,
    ):
        ai_result.pop(
            "agentic_review",
            None,
        )

    return cleaned


def run_deep_agent_review(
    *,
    analysis,
    provider: LLMProvider,
    structured_result:
        dict[str, Any],
    max_steps: int = 6,
) -> dict[str, Any]:

    if not provider.configured:
        return {
            "status": "unavailable",
            "reason":
                "provider_not_configured",
        }

    user = analysis.created_by

    if user is None:
        return {
            "status": "unavailable",
            "reason":
                "analysis_owner_missing",
        }

    runner = AgentRunner(
        user=user,
        provider=provider,
    )

    tools = [
        definition
        for definition
        in build_assistant_tool_definitions(
            user
        )
        if definition.name
        in DEEP_TOOL_NAMES
    ]

    if not tools:
        return {
            "status": "unavailable",
            "reason":
                "deep_review_tools_unavailable",
        }

    compact_result = (
        _compact_structured_result(
            structured_result
        )
    )

    prompt = (
        "VERITAS Deep Analysis review yap.\n\n"
        f"Analysis ID: {analysis.id}\n"
        f"Ana iddia: {analysis.claim_text}\n\n"
        "Structured evidence asamasi:\n"
        + json.dumps(
            compact_result,
            ensure_ascii=False,
            default=str,
        )
    )

    response = (
        provider.generate_with_tools(
            [
                LLMMessage(
                    role="user",
                    content=prompt,
                )
            ],
            tools=tools,
            tool_executor=(
                lambda name, arguments:
                    _execute_deep_tool(
                        runner,
                        name,
                        arguments,
                    )
            ),
            system=
                DEEP_REVIEW_SYSTEM_PROMPT,
            max_steps=max(
                1,
                int(max_steps),
            ),
        )
    )

    metadata = (
        response.metadata
        or {}
    )

    return {
        "status": "completed",
        "provider":
            response.provider,
        "model":
            response.model,
        "transport":
            metadata.get(
                "transport"
            ),
        "output":
            response.text,
        "tool_call_count":
            len(
                response.tool_calls
            ),
        "tool_calls":
            response.tool_calls,
        "input_tokens":
            response.input_tokens,
        "output_tokens":
            response.output_tokens,
        "metadata":
            metadata,
    }



def run_deep_agent_review_with_retry(
    *,
    analysis,
    provider: LLMProvider,
    structured_result:
        dict[str, Any],
    max_steps: int = 6,
    retry_delays:
        tuple[float, ...] = (
            2.0,
            5.0,
        ),
    sleep_fn:
        Callable[[float], None]
        = time.sleep,
) -> dict[str, Any]:
    """
    Claude Agent SDK gibi network/process
    tabanli gecici hatalarda Deep review'u
    kontrollu bicimde yeniden dener.

    Deterministik pipeline sonucu korunur;
    yalnizca agentic review tekrar edilir.
    """

    total_attempts = (
        len(retry_delays) + 1
    )

    for attempt_index in range(
        total_attempts
    ):
        try:
            result = (
                run_deep_agent_review(
                    analysis=analysis,
                    provider=provider,
                    structured_result=
                        structured_result,
                    max_steps=max_steps,
                )
            )

            result[
                "attempt_count"
            ] = attempt_index + 1

            result[
                "retry_count"
            ] = attempt_index

            return result

        except LLMProviderError:
            if (
                attempt_index
                >= len(
                    retry_delays
                )
            ):
                raise

            sleep_fn(
                retry_delays[
                    attempt_index
                ]
            )

    raise RuntimeError(
        "Deep agent retry loop "
        "beklenmeyen bicimde sonlandi."
    )
