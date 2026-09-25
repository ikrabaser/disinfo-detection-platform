from agent.prompts import (
    VERITAS_SYSTEM_PROMPT,
)


def test_prompt_requires_evidence_first_fact_check():
    prompt = (
        VERITAS_SYSTEM_PROMPT
        .lower()
    )

    assert "search_evidence" in prompt
    assert "yetersiz kanit" in prompt
    assert "semantic similarity" in prompt


def test_prompt_does_not_treat_model_score_as_truth():
    prompt = (
        VERITAS_SYSTEM_PROMPT
        .lower()
    )

    assert "truth_score" in prompt
    assert (
        "kesin dogruluk"
        in prompt
    )


def test_prompt_separates_manipulation_from_truth():
    prompt = (
        VERITAS_SYSTEM_PROMPT
        .lower()
    )

    assert (
        "manipulasyon sinyali"
        in prompt
    )

    assert (
        "olgusal dogruluk"
        in prompt
    )
