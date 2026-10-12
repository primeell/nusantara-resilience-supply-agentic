"""Durability, idempotency, and optimistic concurrency regression tests."""

from __future__ import annotations

from backend.repository import SQLiteRepository
from backend.schemas import (
    DecisionAction,
    TransactionDecisionRequest,
    TransactionDraftCreateRequest,
)
from backend.service import (
    InvalidStateTransitionError,
    create_transaction_draft,
    decide_transaction_draft,
    run_deterministic_analysis,
)


def test_sqlite_repository_survives_restart(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "nsra-state.sqlite3"
    repo = SQLiteRepository(db_path=db_path)
    analysis = run_deterministic_analysis(repo, incident_id="INC-MKS-FOUR-DAY")
    request = TransactionDraftCreateRequest(
        incident_id=analysis.incident_id,
        analysis_id=analysis.analysis_id,
        scenario_id=analysis.recommended_scenario_id,
        requested_by="demo.operator",
        idempotency_key="restart-safe-request-001",
    )
    draft = create_transaction_draft(repo, request)

    restored = SQLiteRepository(db_path=db_path)

    assert restored.get_analysis(analysis.analysis_id).recommended_scenario_id == analysis.recommended_scenario_id
    assert restored.latest_analysis_for_incident(analysis.incident_id).analysis_id == analysis.analysis_id  # type: ignore[union-attr]
    assert restored.get_draft(draft.draft_id).idempotency_key == "restart-safe-request-001"
    assert any(item.action == "DRAFT_SUBMITTED" for item in restored.list_audit())


def test_repeated_idempotency_key_returns_one_draft(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repo = SQLiteRepository(db_path=tmp_path / "idempotency.sqlite3")
    analysis = run_deterministic_analysis(repo, incident_id="INC-MKS-FOUR-DAY")
    request = TransactionDraftCreateRequest(
        incident_id=analysis.incident_id,
        analysis_id=analysis.analysis_id,
        scenario_id=analysis.recommended_scenario_id,
        requested_by="demo.operator",
        idempotency_key="same-request-key-001",
    )

    first = create_transaction_draft(repo, request)
    second = create_transaction_draft(repo, request)

    assert second.draft_id == first.draft_id
    assert len(repo.list_drafts()) == 1
    assert [item.action for item in repo.list_audit()].count("DRAFT_CREATED") == 1


def test_decision_uses_version_guard_and_persists(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "decision.sqlite3"
    repo = SQLiteRepository(db_path=db_path)
    analysis = run_deterministic_analysis(repo, incident_id="INC-MKS-FOUR-DAY")
    draft = create_transaction_draft(
        repo,
        TransactionDraftCreateRequest(
            incident_id=analysis.incident_id,
            analysis_id=analysis.analysis_id,
            scenario_id=analysis.recommended_scenario_id,
            requested_by="demo.operator",
            idempotency_key="version-guard-key-001",
        ),
    )

    try:
        decide_transaction_draft(
            repo,
            draft_id=draft.draft_id,
            request=TransactionDecisionRequest(
                action=DecisionAction.APPROVE,
                actor="demo.manager",
                justification="Reviewed with the modeled evidence.",
                expected_version=99,
            ),
        )
    except InvalidStateTransitionError:
        pass
    else:
        raise AssertionError("stale version should be rejected")

    decided = decide_transaction_draft(
        repo,
        draft_id=draft.draft_id,
        request=TransactionDecisionRequest(
            action=DecisionAction.APPROVE,
            actor="demo.manager",
            justification="Reviewed with the modeled evidence.",
            expected_version=1,
        ),
    )
    restored = SQLiteRepository(db_path=db_path).get_draft(draft.draft_id)

    assert decided.version == 2
    assert restored.status.value == "APPROVED"
    assert restored.version == 2
