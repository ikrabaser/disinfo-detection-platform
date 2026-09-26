import pytest

from rest_framework.test import APIClient

from accounts.models import (
    Role,
    User,
)
from analyses.models import (
    Analysis,
    AnalysisModelRun,
    AnalysisModelRunKind,
    AnalysisModelRunSource,
)


def authenticated_client(user):
    client = APIClient()

    client.force_authenticate(
        user=user
    )

    return client


def response_items(response):
    data = response.data

    if (
        isinstance(data, dict)
        and "results" in data
    ):
        return data["results"]

    return data


@pytest.fixture
def analysis_api_data(db):
    admin = User.objects.create_user(
        username="analysis-admin",
        password="pass12345",
        role=Role.ADMIN,
    )

    owner = User.objects.create_user(
        username="analysis-owner",
        password="pass12345",
        role=Role.ANALYST,
    )

    other = User.objects.create_user(
        username="analysis-other",
        password="pass12345",
        role=Role.ANALYST,
    )

    owner_analysis = (
        Analysis.objects.create(
            claim_text="Owner claim",
            created_by=owner,
        )
    )

    other_analysis = (
        Analysis.objects.create(
            claim_text="Other claim",
            created_by=other,
        )
    )

    run = AnalysisModelRun.objects.create(
        analysis=owner_analysis,
        kind=AnalysisModelRunKind.BOT,
        source=(
            AnalysisModelRunSource
            .AGENT_TOOL
        ),
        model_name=(
            "random-forest-test"
        ),
        feature_set="profile-13d",
        graph_id_snapshot=12,
        artifact_ref=(
            "ml_models/test.joblib"
        ),
        result={
            "flagged_count": 0,
        },
        cross_domain=True,
    )

    return {
        "admin": admin,
        "owner": owner,
        "other": other,
        "owner_analysis":
            owner_analysis,
        "other_analysis":
            other_analysis,
        "run": run,
    }


@pytest.mark.django_db
def test_non_admin_analysis_list_is_owner_scoped(
    analysis_api_data,
):
    owner = analysis_api_data[
        "owner"
    ]

    owner_analysis = analysis_api_data[
        "owner_analysis"
    ]

    other_analysis = analysis_api_data[
        "other_analysis"
    ]

    response = (
        authenticated_client(
            owner
        )
        .get(
            "/api/analyses/"
        )
    )

    assert response.status_code == 200

    ids = {
        item["id"]
        for item
        in response_items(response)
    }

    assert (
        owner_analysis.id
        in ids
    )

    assert (
        other_analysis.id
        not in ids
    )


@pytest.mark.django_db
def test_non_owner_cannot_retrieve_analysis(
    analysis_api_data,
):
    owner = analysis_api_data[
        "owner"
    ]

    foreign = analysis_api_data[
        "other_analysis"
    ]

    response = (
        authenticated_client(
            owner
        )
        .get(
            (
                "/api/analyses/"
                f"{foreign.id}/"
            )
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_admin_can_retrieve_any_analysis(
    analysis_api_data,
):
    admin = analysis_api_data[
        "admin"
    ]

    foreign = analysis_api_data[
        "other_analysis"
    ]

    response = (
        authenticated_client(
            admin
        )
        .get(
            (
                "/api/analyses/"
                f"{foreign.id}/"
            )
        )
    )

    assert response.status_code == 200

    assert (
        response.data["id"]
        == foreign.id
    )


@pytest.mark.django_db
def test_owner_can_read_model_run_history(
    analysis_api_data,
):
    owner = analysis_api_data[
        "owner"
    ]

    analysis = analysis_api_data[
        "owner_analysis"
    ]

    run = analysis_api_data[
        "run"
    ]

    response = (
        authenticated_client(
            owner
        )
        .get(
            (
                "/api/analyses/"
                f"{analysis.id}/"
                "model-runs/"
            )
        )
    )

    assert response.status_code == 200
    assert len(response.data) == 1

    item = response.data[0]

    assert item["id"] == run.id

    assert (
        item["kind"]
        == AnalysisModelRunKind.BOT
    )

    assert (
        item["source"]
        == AnalysisModelRunSource
        .AGENT_TOOL
    )

    assert (
        item["model_name"]
        == "random-forest-test"
    )

    assert (
        item["graph_id_snapshot"]
        == 12
    )


@pytest.mark.django_db
def test_non_owner_cannot_read_model_run_history(
    analysis_api_data,
):
    other = analysis_api_data[
        "other"
    ]

    analysis = analysis_api_data[
        "owner_analysis"
    ]

    response = (
        authenticated_client(
            other
        )
        .get(
            (
                "/api/analyses/"
                f"{analysis.id}/"
                "model-runs/"
            )
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_admin_can_read_model_run_history(
    analysis_api_data,
):
    admin = analysis_api_data[
        "admin"
    ]

    analysis = analysis_api_data[
        "owner_analysis"
    ]

    response = (
        authenticated_client(
            admin
        )
        .get(
            (
                "/api/analyses/"
                f"{analysis.id}/"
                "model-runs/"
            )
        )
    )

    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_non_owner_cannot_run_foreign_analysis(
    analysis_api_data,
):
    owner = analysis_api_data[
        "owner"
    ]

    foreign = analysis_api_data[
        "other_analysis"
    ]

    response = (
        authenticated_client(
            owner
        )
        .post(
            (
                "/api/analyses/"
                f"{foreign.id}/run/"
            )
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_owner_can_queue_analysis_and_receives_integer_job_id(
    analysis_api_data,
    monkeypatch,
):
    owner = analysis_api_data[
        "owner"
    ]

    analysis = analysis_api_data[
        "owner_analysis"
    ]

    deferred = {}

    def fake_defer(
        *,
        analysis_id,
    ):
        deferred[
            "analysis_id"
        ] = analysis_id

        return 321

    from analyses import (
        views as analysis_views,
    )

    monkeypatch.setattr(
        analysis_views
        .run_analysis_task,
        "defer",
        fake_defer,
    )

    response = (
        authenticated_client(
            owner
        )
        .post(
            (
                "/api/analyses/"
                f"{analysis.id}/run/"
            )
        )
    )

    assert (
        response.status_code
        == 202
    )

    assert (
        response.data[
            "analysis_id"
        ]
        == analysis.id
    )

    assert (
        response.data[
            "job_id"
        ]
        == 321
    )

    assert (
        deferred[
            "analysis_id"
        ]
        == analysis.id
    )


@pytest.mark.django_db
def test_dashboard_summary_is_owner_scoped(
    analysis_api_data,
):
    owner = analysis_api_data[
        "owner"
    ]

    owner_analysis = (
        analysis_api_data[
            "owner_analysis"
        ]
    )

    owner_analysis.status = (
        "completed"
    )

    owner_analysis.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    response = (
        authenticated_client(
            owner
        )
        .get(
            "/api/analyses/dashboard-summary/"
        )
    )

    assert response.status_code == 200

    assert (
        response.data[
            "counts"
        ][
            "total"
        ]
        == 1
    )

    assert (
        response.data[
            "counts"
        ][
            "completed"
        ]
        == 1
    )

    assert (
        response.data[
            "latest_analysis"
        ][
            "id"
        ]
        == owner_analysis.id
    )


@pytest.mark.django_db
def test_admin_dashboard_summary_includes_all_analyses(
    analysis_api_data,
):
    admin = analysis_api_data[
        "admin"
    ]

    response = (
        authenticated_client(
            admin
        )
        .get(
            "/api/analyses/dashboard-summary/"
        )
    )

    assert response.status_code == 200

    assert (
        response.data[
            "counts"
        ][
            "total"
        ]
        == 2
    )
