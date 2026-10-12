"""Thread-safe repositories with reproducible synthetic seed data."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import RLock
from zoneinfo import ZoneInfo

from backend.schemas import (
    AnalysisResult,
    AuditRecord,
    DraftStatus,
    Incident,
    InventoryRecord,
    Material,
    MitigationOption,
    NetworkLocation,
    PortfolioHistoryPoint,
    Shipment,
    TransactionDraft,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED_PATH = PROJECT_ROOT / "data" / "demo_seed.json"
DEFAULT_STATE_PATH = PROJECT_ROOT / ".nsra-local" / "nsra-state.sqlite3"
DEMO_TIMEZONE = ZoneInfo("Asia/Makassar")


class EntityNotFoundError(LookupError):
    """Raised when a requested demo entity does not exist."""


class InMemoryRepository:
    """Small state store designed for a reliable single-machine demo."""

    def __init__(self, seed_path: Path = DEFAULT_SEED_PATH) -> None:
        self.seed_path = seed_path
        self.storage_name = "memory"
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        """Reload all synthetic fixtures and clear mutable demo state."""

        payload = json.loads(self.seed_path.read_text(encoding="utf-8"))
        with self._lock:
            self.demo_now = datetime.fromisoformat(payload["demo_now"])
            self.materials = {
                item["material_id"]: Material.model_validate(item)
                for item in payload["materials"]
            }
            self.inventory = {
                (item["material_id"], item["facility_id"]): InventoryRecord.model_validate(item)
                for item in payload["inventory"]
            }
            self.shipments = {
                item["shipment_id"]: Shipment.model_validate(item)
                for item in payload["shipments"]
            }
            self.incidents = {
                item["incident_id"]: Incident.model_validate(item)
                for item in payload["incidents"]
            }
            self.options = [
                MitigationOption.model_validate(item)
                for item in payload["mitigation_options"]
            ]
            self.locations = {
                item["location_id"]: NetworkLocation.model_validate(item)
                for item in payload.get("locations", [])
            }
            self.portfolio_history = [
                PortfolioHistoryPoint.model_validate(item)
                for item in payload.get("portfolio_history", [])
            ]
            self.analyses: dict[str, AnalysisResult] = {}
            self.drafts: dict[str, TransactionDraft] = {}
            self.audit_records: list[AuditRecord] = []
            self._draft_counter = 0
            self._audit_counter = 0
            self.record_audit(
                action="DEMO_RESET",
                actor="system",
                entity_type="demo",
                entity_id="seed",
                incident_id=None,
                summary="Synthetic demo dataset loaded",
                timestamp=self.demo_now,
            )

    def list_inventory(self) -> list[InventoryRecord]:
        return [item.model_copy(deep=True) for item in self.inventory.values()]

    def list_locations(self) -> list[NetworkLocation]:
        return [item.model_copy(deep=True) for item in self.locations.values()]

    def list_portfolio_history(self) -> list[PortfolioHistoryPoint]:
        return [item.model_copy(deep=True) for item in self.portfolio_history]

    def get_inventory(self, material_id: str, facility_id: str) -> InventoryRecord:
        item = self.inventory.get((material_id, facility_id))
        if item is None:
            raise EntityNotFoundError(
                f"Inventory not found for material={material_id} facility={facility_id}"
            )
        return item.model_copy(deep=True)

    def find_inventory(
        self, material_id: str, facility_id: str
    ) -> InventoryRecord | None:
        """Return an optional inventory position for adapter-level constraints."""

        item = self.inventory.get((material_id, facility_id))
        return item.model_copy(deep=True) if item is not None else None

    def list_shipments(self) -> list[Shipment]:
        return [item.model_copy(deep=True) for item in self.shipments.values()]

    def get_shipment(self, shipment_id: str) -> Shipment:
        item = self.shipments.get(shipment_id)
        if item is None:
            raise EntityNotFoundError(f"Shipment not found: {shipment_id}")
        return item.model_copy(deep=True)

    def find_shipment(self, material_id: str, facility_id: str) -> Shipment:
        for item in self.shipments.values():
            if (
                item.material_id == material_id
                and item.destination_facility_id == facility_id
            ):
                return item.model_copy(deep=True)
        raise EntityNotFoundError(
            f"Shipment not found for material={material_id} facility={facility_id}"
        )

    def list_incidents(self) -> list[Incident]:
        return [item.model_copy(deep=True) for item in self.incidents.values()]

    def get_incident(self, incident_id: str) -> Incident:
        item = self.incidents.get(incident_id)
        if item is None:
            raise EntityNotFoundError(f"Incident not found: {incident_id}")
        return item.model_copy(deep=True)

    def upsert_incident(self, incident: Incident) -> tuple[Incident, bool]:
        with self._lock:
            current = self.incidents.get(incident.incident_id)
            if current is not None:
                return current.model_copy(deep=True), False
            self.incidents[incident.incident_id] = incident
            self.record_audit(
                action="INCIDENT_INGESTED",
                actor="event-adapter",
                entity_type="incident",
                entity_id=incident.incident_id,
                incident_id=incident.incident_id,
                summary=f"Incident accepted from {incident.source}",
            )
            return incident.model_copy(deep=True), True

    def options_for_incident(self, incident_id: str) -> list[MitigationOption]:
        return [
            item.model_copy(deep=True)
            for item in self.options
            if item.incident_id == incident_id
        ]

    def save_analysis(self, analysis: AnalysisResult) -> None:
        with self._lock:
            self.analyses[analysis.analysis_id] = analysis
            self.record_audit(
                action="ANALYSIS_COMPLETED",
                actor="nsra-engine",
                entity_type="analysis",
                entity_id=analysis.analysis_id,
                incident_id=analysis.incident_id,
                summary=(
                    f"Recommended {analysis.recommended_scenario_id} in {analysis.mode.value} mode"
                ),
            )

    def get_analysis(self, analysis_id: str) -> AnalysisResult:
        item = self.analyses.get(analysis_id)
        if item is None:
            raise EntityNotFoundError(f"Analysis not found: {analysis_id}")
        return item.model_copy(deep=True)

    def latest_analysis_for_incident(
        self, incident_id: str
    ) -> AnalysisResult | None:
        matches = [
            item for item in self.analyses.values() if item.incident_id == incident_id
        ]
        if not matches:
            return None
        latest = max(matches, key=lambda item: item.generated_at)
        return latest.model_copy(deep=True)

    def next_draft_id(self) -> str:
        with self._lock:
            self._draft_counter += 1
            return f"DRF-{self._draft_counter:04d}"

    def save_draft(self, draft: TransactionDraft) -> None:
        with self._lock:
            self.drafts[draft.draft_id] = draft

    def find_draft_by_idempotency_key(
        self, idempotency_key: str | None
    ) -> TransactionDraft | None:
        if not idempotency_key:
            return None
        with self._lock:
            for draft in self.drafts.values():
                if draft.idempotency_key == idempotency_key:
                    return draft.model_copy(deep=True)
        return None

    def save_draft_if_idempotency_absent(
        self, draft: TransactionDraft
    ) -> tuple[TransactionDraft, bool]:
        """Atomically save a draft or return the existing idempotent result."""

        with self._lock:
            existing = self.find_draft_by_idempotency_key(draft.idempotency_key)
            if existing is not None:
                return existing, False
            self.drafts[draft.draft_id] = draft
            return draft.model_copy(deep=True), True

    def save_draft_if_current(
        self,
        draft: TransactionDraft,
        *,
        expected_version: int,
        expected_status: DraftStatus,
    ) -> bool:
        """Atomically replace a draft only when its state still matches."""

        with self._lock:
            current = self.drafts.get(draft.draft_id)
            if (
                current is None
                or current.version != expected_version
                or current.status != expected_status
            ):
                return False
            self.drafts[draft.draft_id] = draft
            return True

    def get_draft(self, draft_id: str) -> TransactionDraft:
        item = self.drafts.get(draft_id)
        if item is None:
            raise EntityNotFoundError(f"Transaction draft not found: {draft_id}")
        return item.model_copy(deep=True)

    def list_drafts(self) -> list[TransactionDraft]:
        return [item.model_copy(deep=True) for item in self.drafts.values()]

    def record_audit(
        self,
        *,
        action: str,
        actor: str,
        entity_type: str,
        entity_id: str,
        incident_id: str | None,
        summary: str,
        timestamp: datetime | None = None,
    ) -> AuditRecord:
        with self._lock:
            self._audit_counter += 1
            record = AuditRecord(
                audit_id=f"AUD-{self._audit_counter:05d}",
                timestamp=timestamp or datetime.now(DEMO_TIMEZONE),
                action=action,
                actor=actor,
                entity_type=entity_type,
                entity_id=entity_id,
                incident_id=incident_id,
                summary=summary,
            )
            self.audit_records.append(record)
            return record.model_copy(deep=True)

    def list_audit(self, incident_id: str | None = None) -> list[AuditRecord]:
        records = self.audit_records
        if incident_id is not None:
            records = [item for item in records if item.incident_id == incident_id]
        return [item.model_copy(deep=True) for item in records]


class SQLiteRepository(InMemoryRepository):
    """Small durable state store for the single-machine competition demo.

    Reference fixtures still come from the reviewed JSON seed. Mutable incidents,
    analyses, drafts, counters, and audit records are persisted as validated JSON
    snapshots in SQLite so a backend restart does not erase the decision trail.
    """

    def __init__(
        self,
        seed_path: Path = DEFAULT_SEED_PATH,
        db_path: Path = DEFAULT_STATE_PATH,
    ) -> None:
        self.db_path = db_path
        self._database_ready = False
        super().__init__(seed_path=seed_path)
        self.storage_name = "sqlite"
        self._ensure_schema()
        self._database_ready = True
        if not self._restore_state():
            self._persist_state()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS entity_state (
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (entity_type, entity_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS repository_meta (
                    meta_key TEXT PRIMARY KEY,
                    meta_value TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _payload(model: object) -> str:
        return json.dumps(model.model_dump(mode="json"), separators=(",", ":"))  # type: ignore[attr-defined]

    def _persist_state(self) -> None:
        if not getattr(self, "_database_ready", False):
            return
        with self._lock:
            rows: list[tuple[str, str, str]] = []
            rows.extend(
                ("incident", key, self._payload(value))
                for key, value in self.incidents.items()
            )
            rows.extend(
                ("analysis", key, self._payload(value))
                for key, value in self.analyses.items()
            )
            rows.extend(
                ("draft", key, self._payload(value))
                for key, value in self.drafts.items()
            )
            rows.extend(
                ("audit", value.audit_id, self._payload(value))
                for value in self.audit_records
            )
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("DELETE FROM entity_state")
                connection.executemany(
                    "INSERT INTO entity_state(entity_type, entity_id, payload) VALUES (?, ?, ?)",
                    rows,
                )
                connection.execute("DELETE FROM repository_meta")
                connection.executemany(
                    "INSERT INTO repository_meta(meta_key, meta_value) VALUES (?, ?)",
                    [
                        ("initialized", "1"),
                        ("draft_counter", str(self._draft_counter)),
                        ("audit_counter", str(self._audit_counter)),
                    ],
                )

    def _restore_state(self) -> bool:
        with self._connect() as connection:
            meta = dict(connection.execute("SELECT meta_key, meta_value FROM repository_meta"))
            if meta.get("initialized") != "1":
                return False
            rows = connection.execute(
                "SELECT entity_type, entity_id, payload FROM entity_state"
            ).fetchall()

        grouped: dict[str, list[tuple[str, str]]] = {}
        for entity_type, entity_id, payload in rows:
            grouped.setdefault(entity_type, []).append((entity_id, payload))

        with self._lock:
            self.incidents = {
                entity_id: Incident.model_validate_json(payload)
                for entity_id, payload in grouped.get("incident", [])
            }
            self.analyses = {
                entity_id: AnalysisResult.model_validate_json(payload)
                for entity_id, payload in grouped.get("analysis", [])
            }
            self.drafts = {
                entity_id: TransactionDraft.model_validate_json(payload)
                for entity_id, payload in grouped.get("draft", [])
            }
            self.audit_records = [
                AuditRecord.model_validate_json(payload)
                for _, payload in sorted(grouped.get("audit", []))
            ]
            self._draft_counter = int(meta.get("draft_counter", "0"))
            self._audit_counter = int(meta.get("audit_counter", "0"))
        return True

    def reset(self) -> None:
        super().reset()
        self._persist_state()

    def upsert_incident(self, incident: Incident) -> tuple[Incident, bool]:
        result = super().upsert_incident(incident)
        if result[1]:
            self._persist_state()
        return result

    def save_analysis(self, analysis: AnalysisResult) -> None:
        super().save_analysis(analysis)
        self._persist_state()

    def next_draft_id(self) -> str:
        draft_id = super().next_draft_id()
        self._persist_state()
        return draft_id

    def save_draft(self, draft: TransactionDraft) -> None:
        super().save_draft(draft)
        self._persist_state()

    def save_draft_if_idempotency_absent(
        self, draft: TransactionDraft
    ) -> tuple[TransactionDraft, bool]:
        result = super().save_draft_if_idempotency_absent(draft)
        if result[1]:
            self._persist_state()
        return result

    def save_draft_if_current(
        self,
        draft: TransactionDraft,
        *,
        expected_version: int,
        expected_status: DraftStatus,
    ) -> bool:
        saved = super().save_draft_if_current(
            draft,
            expected_version=expected_version,
            expected_status=expected_status,
        )
        if saved:
            self._persist_state()
        return saved

    def record_audit(
        self,
        *,
        action: str,
        actor: str,
        entity_type: str,
        entity_id: str,
        incident_id: str | None,
        summary: str,
        timestamp: datetime | None = None,
    ) -> AuditRecord:
        record = super().record_audit(
            action=action,
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            incident_id=incident_id,
            summary=summary,
            timestamp=timestamp,
        )
        self._persist_state()
        return record


class PostgreSQLRepository(SQLiteRepository):
    """Cloud-durable snapshot repository backed by PostgreSQL.

    The public repository contract remains identical to the local SQLite store,
    which keeps the deterministic workflow and approval semantics unchanged.
    Cloud Foundry can supply the DSN through ``DATABASE_URL`` or a bound
    PostgreSQL service in ``VCAP_SERVICES``.
    """

    def __init__(
        self,
        dsn: str,
        seed_path: Path = DEFAULT_SEED_PATH,
    ) -> None:
        self.dsn = dsn
        self._database_ready = False
        InMemoryRepository.__init__(self, seed_path=seed_path)
        self.storage_name = "postgresql"
        self._ensure_schema()
        self._database_ready = True
        if not self._restore_state():
            self._persist_state()

    def _connect(self):  # type: ignore[no-untyped-def]
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - cloud misconfiguration only
            raise RuntimeError(
                "PostgreSQL is configured but psycopg is not installed"
            ) from exc
        return psycopg.connect(self.dsn, connect_timeout=10)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS entity_state (
                        entity_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        PRIMARY KEY (entity_type, entity_id)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS repository_meta (
                        meta_key TEXT PRIMARY KEY,
                        meta_value TEXT NOT NULL
                    )
                    """
                )

    def _persist_state(self) -> None:
        if not getattr(self, "_database_ready", False):
            return
        with self._lock:
            rows: list[tuple[str, str, str]] = []
            rows.extend(
                ("incident", key, self._payload(value))
                for key, value in self.incidents.items()
            )
            rows.extend(
                ("analysis", key, self._payload(value))
                for key, value in self.analyses.items()
            )
            rows.extend(
                ("draft", key, self._payload(value))
                for key, value in self.drafts.items()
            )
            rows.extend(
                ("audit", value.audit_id, self._payload(value))
                for value in self.audit_records
            )
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("DELETE FROM entity_state")
                    cursor.executemany(
                        """
                        INSERT INTO entity_state(entity_type, entity_id, payload)
                        VALUES (%s, %s, %s)
                        """,
                        rows,
                    )
                    cursor.execute("DELETE FROM repository_meta")
                    cursor.executemany(
                        """
                        INSERT INTO repository_meta(meta_key, meta_value)
                        VALUES (%s, %s)
                        """,
                        [
                            ("initialized", "1"),
                            ("draft_counter", str(self._draft_counter)),
                            ("audit_counter", str(self._audit_counter)),
                        ],
                    )

    def _restore_state(self) -> bool:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT meta_key, meta_value FROM repository_meta")
                meta = dict(cursor.fetchall())
                if meta.get("initialized") != "1":
                    return False
                cursor.execute(
                    "SELECT entity_type, entity_id, payload FROM entity_state"
                )
                rows = cursor.fetchall()

        grouped: dict[str, list[tuple[str, str]]] = {}
        for entity_type, entity_id, payload in rows:
            grouped.setdefault(entity_type, []).append((entity_id, payload))

        with self._lock:
            self.incidents = {
                entity_id: Incident.model_validate_json(payload)
                for entity_id, payload in grouped.get("incident", [])
            }
            self.analyses = {
                entity_id: AnalysisResult.model_validate_json(payload)
                for entity_id, payload in grouped.get("analysis", [])
            }
            self.drafts = {
                entity_id: TransactionDraft.model_validate_json(payload)
                for entity_id, payload in grouped.get("draft", [])
            }
            self.audit_records = [
                AuditRecord.model_validate_json(payload)
                for _, payload in sorted(grouped.get("audit", []))
            ]
            self._draft_counter = int(meta.get("draft_counter", "0"))
            self._audit_counter = int(meta.get("audit_counter", "0"))
        return True


def _state_path_from_env() -> Path:
    configured = os.getenv("NSRA_STATE_DB_PATH")
    return Path(configured).expanduser() if configured else DEFAULT_STATE_PATH


def _postgres_dsn_from_env() -> str | None:
    direct = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if direct:
        return direct

    raw_services = os.getenv("VCAP_SERVICES")
    if not raw_services:
        return None
    try:
        services = json.loads(raw_services)
    except json.JSONDecodeError:
        return None

    for label, instances in services.items():
        for instance in instances:
            marker = " ".join(
                [
                    str(label),
                    str(instance.get("label", "")),
                    str(instance.get("name", "")),
                    " ".join(instance.get("tags", [])),
                ]
            ).lower()
            if "postgres" not in marker:
                continue
            credentials = instance.get("credentials", {})
            for key in ("uri", "url", "connectionString", "database_url"):
                value = credentials.get(key)
                if value:
                    return str(value)
    return None


def build_repository() -> InMemoryRepository:
    postgres_dsn = _postgres_dsn_from_env()
    if postgres_dsn:
        return PostgreSQLRepository(dsn=postgres_dsn)
    return SQLiteRepository(db_path=_state_path_from_env())


repository = build_repository()
