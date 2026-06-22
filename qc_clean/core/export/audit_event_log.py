"""Local hash-linked event log for export audit operations."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


ExportAuditEventType = Literal[
    "manifest_written",
    "manifest_verified",
    "publish_preflight",
]
ExportAuditEventLogStatus = Literal["verified", "invalid"]
ExportAuditEventDbMirrorStatus = Literal["mirrored"]
ExportAuditEventDbVerificationStatus = Literal["verified", "invalid"]

EXPORT_AUDIT_EVENT_LOG_CAVEAT = (
    "Export audit event logs are local hash-linked provenance metadata only; "
    "they are not signing, not immutable storage, not external timestamping, "
    "not a complete tamper-evident audit substrate, and not methodological "
    "validity evidence."
)


class ExportAuditEvent(BaseModel):
    """One local export-audit event record."""

    schema_version: Literal[1] = Field(description="Export audit event schema version")
    package_type: Literal["export_audit_event"] = Field(description="Event package kind")
    event_type: ExportAuditEventType = Field(description="Export audit event type")
    event_status: str = Field(description="Native status reported by the audited operation")
    created_at: str = Field(description="UTC timestamp when the event was appended")
    manifest_path: str | None = Field(
        default=None,
        description="Manifest path associated with the event when available",
    )
    manifest_file_sha256: str | None = Field(
        default=None,
        description="SHA-256 hash of the manifest file bytes when available",
    )
    payload_sha256: str = Field(description="SHA-256 hash of the event source payload")
    previous_event_sha256: str | None = Field(
        default=None,
        description="Hash of the preceding event in the same local log",
    )
    event_sha256: str = Field(description="SHA-256 of this event with this field blanked")
    caveat: str = Field(description="Claim-discipline caveat for local event logging")


class ExportAuditEventLogFailure(BaseModel):
    """One export audit event-log verification failure."""

    code: str = Field(description="Stable event-log verification failure code")
    line_number: int | None = Field(
        default=None,
        description="One-based JSONL line number when applicable",
    )
    field: str = Field(description="Event-log field that failed verification")
    expected: str | None = Field(default=None, description="Expected value")
    actual: str | None = Field(default=None, description="Actual value")
    message: str = Field(description="Human-readable verification failure")


class ExportAuditEventLogVerificationReport(BaseModel):
    """Verification report for a local export audit event log."""

    schema_version: Literal[1] = Field(
        description="Event-log verification report schema version"
    )
    package_type: Literal["export_audit_event_log_verification"] = Field(
        description="Event-log verification report package kind"
    )
    status: ExportAuditEventLogStatus = Field(description="Overall verification status")
    log_path: str = Field(description="Event log path checked")
    event_count: int = Field(description="Number of non-empty JSONL event lines")
    checked_event_count: int = Field(description="Number of event lines with valid shape")
    failure_count: int = Field(description="Number of event-log verification failures")
    failures: list[ExportAuditEventLogFailure] = Field(
        description="Structured event-log verification failures"
    )
    caveat: str = Field(description="Claim-discipline caveat for event-log verification")


class ExportAuditEventDbMirrorReport(BaseModel):
    """Report from mirroring a local export audit JSONL log into SQLite."""

    schema_version: Literal[1] = Field(description="SQLite mirror report schema version")
    package_type: Literal["export_audit_event_db_mirror"] = Field(
        description="SQLite mirror report package kind"
    )
    status: ExportAuditEventDbMirrorStatus = Field(description="Overall mirror status")
    source_log_path: str = Field(description="Source JSONL event-log path")
    db_path: str = Field(description="SQLite database path written")
    source_event_count: int = Field(description="Verified source JSONL event count")
    inserted_event_count: int = Field(description="Number of new events inserted")
    total_event_count: int = Field(description="Total events now stored in SQLite")
    caveat: str = Field(description="Claim-discipline caveat for DB event mirrors")


class ExportAuditEventDbVerificationFailure(BaseModel):
    """One SQLite audit-event verification failure."""

    code: str = Field(description="Stable SQLite verification failure code")
    row_sequence: int | None = Field(
        default=None,
        description="SQLite event row sequence when applicable",
    )
    field: str = Field(description="SQLite event field that failed verification")
    expected: str | None = Field(default=None, description="Expected value")
    actual: str | None = Field(default=None, description="Actual value")
    message: str = Field(description="Human-readable verification failure")


class ExportAuditEventDbVerificationReport(BaseModel):
    """Verification report for a local SQLite export audit event mirror."""

    schema_version: Literal[1] = Field(
        description="SQLite event verification report schema version"
    )
    package_type: Literal["export_audit_event_db_verification"] = Field(
        description="SQLite event verification report package kind"
    )
    status: ExportAuditEventDbVerificationStatus = Field(
        description="Overall SQLite verification status"
    )
    db_path: str = Field(description="SQLite database path checked")
    event_count: int = Field(description="Number of SQLite event rows")
    checked_event_count: int = Field(description="Number of event rows with valid shape")
    failure_count: int = Field(description="Number of SQLite verification failures")
    failures: list[ExportAuditEventDbVerificationFailure] = Field(
        description="Structured SQLite verification failures"
    )
    caveat: str = Field(description="Claim-discipline caveat for DB event verification")


def append_export_audit_event(
    log_path: str | Path,
    *,
    event_type: ExportAuditEventType,
    event_status: str,
    manifest_path: str | Path | None = None,
    payload: object | None = None,
) -> ExportAuditEvent:
    """Append one hash-linked export audit event to a local JSONL log."""
    path = Path(log_path)
    previous_event_sha256 = _previous_event_sha256(path)
    manifest_path_str = str(manifest_path) if manifest_path is not None else None

    event = ExportAuditEvent(
        schema_version=1,
        package_type="export_audit_event",
        event_type=event_type,
        event_status=event_status,
        created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        manifest_path=manifest_path_str,
        manifest_file_sha256=_file_sha256(Path(manifest_path)) if manifest_path else None,
        payload_sha256=_sha256_jsonable(payload),
        previous_event_sha256=previous_event_sha256,
        event_sha256="",
        caveat=EXPORT_AUDIT_EVENT_LOG_CAVEAT,
    )
    event.event_sha256 = _event_hash(event)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False))
        handle.write("\n")
    return event


def mirror_export_audit_event_log_to_sqlite(
    log_path: str | Path,
    db_path: str | Path,
) -> ExportAuditEventDbMirrorReport:
    """Mirror a verified local JSONL export audit log into SQLite."""
    source_path = Path(log_path)
    database_path = Path(db_path)
    source_report = verify_export_audit_event_log(source_path)
    if source_report.status != "verified":
        raise ValueError(
            f"Cannot mirror invalid export audit event log '{source_path}': "
            f"{source_report.failure_count} verification failure(s)"
        )

    if database_path.exists():
        db_report = verify_export_audit_event_db(database_path)
        if db_report.status != "verified":
            raise ValueError(
                f"Cannot mirror into invalid export audit event database "
                f"'{database_path}': {db_report.failure_count} verification failure(s)"
            )

    events = _load_verified_export_audit_events(source_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    inserted = 0
    with sqlite3.connect(database_path) as conn:
        _ensure_event_db_schema(conn)
        for event in events:
            payload = event.model_dump(mode="json")
            payload_json = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO export_audit_events (
                    event_sha256,
                    previous_event_sha256,
                    event_type,
                    event_status,
                    created_at,
                    manifest_path,
                    event_payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_sha256,
                    event.previous_event_sha256,
                    event.event_type,
                    event.event_status,
                    event.created_at,
                    event.manifest_path,
                    payload_json,
                ),
            )
            inserted += cursor.rowcount
        total = _event_db_count(conn)

    return ExportAuditEventDbMirrorReport(
        schema_version=1,
        package_type="export_audit_event_db_mirror",
        status="mirrored",
        source_log_path=str(source_path),
        db_path=str(database_path),
        source_event_count=source_report.event_count,
        inserted_event_count=inserted,
        total_event_count=total,
        caveat=EXPORT_AUDIT_EVENT_LOG_CAVEAT,
    )


def verify_export_audit_event_log(
    log_path: str | Path,
) -> ExportAuditEventLogVerificationReport:
    """Verify local event hashes and previous-event links in an export audit log."""
    path = Path(log_path)
    if not path.exists():
        failure = ExportAuditEventLogFailure(
            code="log_missing",
            field="log_path",
            expected="file exists",
            actual="missing",
            message="Export audit event log does not exist",
        )
        return _verification_report(path, event_count=0, checked_event_count=0, failures=[failure])
    if not path.is_file():
        failure = ExportAuditEventLogFailure(
            code="log_not_file",
            field="log_path",
            expected="file",
            actual="not_file",
            message="Export audit event log path is not a file",
        )
        return _verification_report(path, event_count=0, checked_event_count=0, failures=[failure])

    failures: list[ExportAuditEventLogFailure] = []
    event_count = 0
    checked_event_count = 0
    expected_previous_hash: str | None = None

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        event_count += 1
        try:
            raw_event = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(
                ExportAuditEventLogFailure(
                    code="invalid_json",
                    line_number=line_number,
                    field="event",
                    message=f"Event log line is not valid JSON: {exc}",
                )
            )
            continue
        if not isinstance(raw_event, dict):
            failures.append(
                ExportAuditEventLogFailure(
                    code="invalid_event_payload",
                    line_number=line_number,
                    field="event",
                    actual=type(raw_event).__name__,
                    message="Event log line must be a JSON object",
                )
            )
            continue
        try:
            event = ExportAuditEvent.model_validate(raw_event)
        except ValidationError as exc:
            failures.append(
                ExportAuditEventLogFailure(
                    code="invalid_event_shape",
                    line_number=line_number,
                    field="event",
                    message=f"Event has invalid shape: {exc}",
                )
            )
            continue

        checked_event_count += 1
        actual_event_hash = _event_payload_hash(raw_event)
        if actual_event_hash != event.event_sha256:
            failures.append(
                ExportAuditEventLogFailure(
                    code="event_sha256_mismatch",
                    line_number=line_number,
                    field="event_sha256",
                    expected=event.event_sha256,
                    actual=actual_event_hash,
                    message="Event self-hash does not match event content",
                )
            )
        if event.previous_event_sha256 != expected_previous_hash:
            failures.append(
                ExportAuditEventLogFailure(
                    code="previous_event_sha256_mismatch",
                    line_number=line_number,
                    field="previous_event_sha256",
                    expected=expected_previous_hash,
                    actual=event.previous_event_sha256,
                    message="Event previous-hash link does not match the prior event",
                )
            )
        expected_previous_hash = event.event_sha256

    return _verification_report(
        path,
        event_count=event_count,
        checked_event_count=checked_event_count,
        failures=failures,
    )


def verify_export_audit_event_db(
    db_path: str | Path,
) -> ExportAuditEventDbVerificationReport:
    """Verify local SQLite event payload hashes and previous-event links."""
    path = Path(db_path)
    if not path.exists():
        failure = ExportAuditEventDbVerificationFailure(
            code="db_missing",
            field="db_path",
            expected="file exists",
            actual="missing",
            message="Export audit event SQLite database does not exist",
        )
        return _db_verification_report(
            path,
            event_count=0,
            checked_event_count=0,
            failures=[failure],
        )
    if not path.is_file():
        failure = ExportAuditEventDbVerificationFailure(
            code="db_not_file",
            field="db_path",
            expected="file",
            actual="not_file",
            message="Export audit event SQLite path is not a file",
        )
        return _db_verification_report(
            path,
            event_count=0,
            checked_event_count=0,
            failures=[failure],
        )

    failures: list[ExportAuditEventDbVerificationFailure] = []
    event_count = 0
    checked_event_count = 0
    expected_previous_hash: str | None = None
    seen_hashes: set[str] = set()

    try:
        with sqlite3.connect(path) as conn:
            if not _event_db_table_exists(conn):
                failures.append(ExportAuditEventDbVerificationFailure(
                    code="table_missing",
                    field="export_audit_events",
                    expected="table exists",
                    actual="missing",
                    message="SQLite audit event table does not exist",
                ))
                return _db_verification_report(
                    path,
                    event_count=0,
                    checked_event_count=0,
                    failures=failures,
                )
            rows = conn.execute(
                """
                SELECT sequence, event_sha256, previous_event_sha256, event_payload_json
                FROM export_audit_events
                ORDER BY sequence
                """
            ).fetchall()
    except sqlite3.DatabaseError as exc:
        failures.append(ExportAuditEventDbVerificationFailure(
            code="db_error",
            field="db_path",
            message=f"Could not read SQLite audit event database: {exc}",
        ))
        return _db_verification_report(
            path,
            event_count=0,
            checked_event_count=0,
            failures=failures,
        )

    for sequence, row_hash, row_previous_hash, payload_json in rows:
        event_count += 1
        try:
            raw_event = json.loads(payload_json)
        except json.JSONDecodeError as exc:
            failures.append(ExportAuditEventDbVerificationFailure(
                code="invalid_json",
                row_sequence=sequence,
                field="event_payload_json",
                message=f"SQLite event payload is not valid JSON: {exc}",
            ))
            continue
        if not isinstance(raw_event, dict):
            failures.append(ExportAuditEventDbVerificationFailure(
                code="invalid_event_payload",
                row_sequence=sequence,
                field="event_payload_json",
                actual=type(raw_event).__name__,
                message="SQLite event payload must be a JSON object",
            ))
            continue
        try:
            event = ExportAuditEvent.model_validate(raw_event)
        except ValidationError as exc:
            failures.append(ExportAuditEventDbVerificationFailure(
                code="invalid_event_shape",
                row_sequence=sequence,
                field="event_payload_json",
                message=f"SQLite event payload has invalid shape: {exc}",
            ))
            continue

        checked_event_count += 1
        actual_event_hash = _event_payload_hash(raw_event)
        if event.event_sha256 in seen_hashes:
            failures.append(ExportAuditEventDbVerificationFailure(
                code="duplicate_event_sha256",
                row_sequence=sequence,
                field="event_sha256",
                actual=event.event_sha256,
                message="SQLite event hash appears more than once",
            ))
        seen_hashes.add(event.event_sha256)
        if row_hash != event.event_sha256:
            failures.append(ExportAuditEventDbVerificationFailure(
                code="row_event_sha256_mismatch",
                row_sequence=sequence,
                field="event_sha256",
                expected=event.event_sha256,
                actual=row_hash,
                message="SQLite event hash column does not match payload",
            ))
        if actual_event_hash != event.event_sha256:
            failures.append(ExportAuditEventDbVerificationFailure(
                code="event_sha256_mismatch",
                row_sequence=sequence,
                field="event_sha256",
                expected=event.event_sha256,
                actual=actual_event_hash,
                message="SQLite event self-hash does not match event content",
            ))
        if row_previous_hash != event.previous_event_sha256:
            failures.append(ExportAuditEventDbVerificationFailure(
                code="row_previous_event_sha256_mismatch",
                row_sequence=sequence,
                field="previous_event_sha256",
                expected=event.previous_event_sha256,
                actual=row_previous_hash,
                message="SQLite previous-hash column does not match payload",
            ))
        if event.previous_event_sha256 != expected_previous_hash:
            failures.append(ExportAuditEventDbVerificationFailure(
                code="previous_event_sha256_mismatch",
                row_sequence=sequence,
                field="previous_event_sha256",
                expected=expected_previous_hash,
                actual=event.previous_event_sha256,
                message="SQLite event previous-hash link does not match row order",
            ))
        expected_previous_hash = event.event_sha256

    return _db_verification_report(
        path,
        event_count=event_count,
        checked_event_count=checked_event_count,
        failures=failures,
    )


def _previous_event_sha256(log_path: Path) -> str | None:
    """Return the prior event hash, failing loud if an existing log is invalid."""
    if not log_path.exists():
        return None
    report = verify_export_audit_event_log(log_path)
    if report.status != "verified":
        raise ValueError(
            f"Cannot append to invalid export audit event log '{log_path}': "
            f"{report.failure_count} verification failure(s)"
        )

    for line in reversed(log_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        raw_event = json.loads(line)
        event = ExportAuditEvent.model_validate(raw_event)
        return event.event_sha256
    return None


def _verification_report(
    log_path: Path,
    *,
    event_count: int,
    checked_event_count: int,
    failures: list[ExportAuditEventLogFailure],
) -> ExportAuditEventLogVerificationReport:
    """Build an event-log verification report with consistent caveat text."""
    return ExportAuditEventLogVerificationReport(
        schema_version=1,
        package_type="export_audit_event_log_verification",
        status="invalid" if failures else "verified",
        log_path=str(log_path),
        event_count=event_count,
        checked_event_count=checked_event_count,
        failure_count=len(failures),
        failures=failures,
        caveat=EXPORT_AUDIT_EVENT_LOG_CAVEAT,
    )


def _db_verification_report(
    db_path: Path,
    *,
    event_count: int,
    checked_event_count: int,
    failures: list[ExportAuditEventDbVerificationFailure],
) -> ExportAuditEventDbVerificationReport:
    """Build a SQLite event verification report with consistent caveat text."""
    return ExportAuditEventDbVerificationReport(
        schema_version=1,
        package_type="export_audit_event_db_verification",
        status="invalid" if failures else "verified",
        db_path=str(db_path),
        event_count=event_count,
        checked_event_count=checked_event_count,
        failure_count=len(failures),
        failures=failures,
        caveat=EXPORT_AUDIT_EVENT_LOG_CAVEAT,
    )


def _load_verified_export_audit_events(log_path: Path) -> list[ExportAuditEvent]:
    """Load event models from a verified JSONL event log."""
    events: list[ExportAuditEvent] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(ExportAuditEvent.model_validate(json.loads(line)))
    return events


def _ensure_event_db_schema(conn: sqlite3.Connection) -> None:
    """Create the local SQLite event mirror schema if needed."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS export_audit_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            event_sha256 TEXT NOT NULL UNIQUE,
            previous_event_sha256 TEXT,
            event_type TEXT NOT NULL,
            event_status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            manifest_path TEXT,
            event_payload_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_export_audit_events_created_at
        ON export_audit_events(created_at)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_export_audit_events_type
        ON export_audit_events(event_type)
        """
    )


def _event_db_table_exists(conn: sqlite3.Connection) -> bool:
    """Return whether the SQLite audit event table exists."""
    row = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'export_audit_events'
        """
    ).fetchone()
    return row is not None


def _event_db_count(conn: sqlite3.Connection) -> int:
    """Return the number of mirrored SQLite audit events."""
    row = conn.execute("SELECT COUNT(*) FROM export_audit_events").fetchone()
    return int(row[0])


def _event_hash(event: ExportAuditEvent) -> str:
    """Return the self-hash for an event model."""
    return _event_payload_hash(event.model_dump(mode="json"))


def _event_payload_hash(payload: dict[str, object]) -> str:
    """Return the self-hash for an event payload."""
    event_without_hash = dict(payload)
    event_without_hash["event_sha256"] = ""
    return _sha256_jsonable(event_without_hash)


def _file_sha256(path: Path) -> str | None:
    """Return a file SHA-256 when the file exists."""
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_jsonable(value: object) -> str:
    """Return a deterministic SHA-256 hash for a JSON-serializable value."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
