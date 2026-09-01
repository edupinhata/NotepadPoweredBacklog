#!/usr/bin/env python
"""Privacy-preserving AI usage accounting for one development work unit."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import csv
import io
import tempfile
import subprocess
import sys
import time
from contextlib import closing
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
WORK_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
TECHNICAL_VALUE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/+-]{0,127}\Z")
FEATURE_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._:/+()-]{0,127}\Z")
NOTE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .,:;_+()/+-]{0,255}\Z")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
MEASUREMENT_BOUNDARIES = {
    "development-through-final-local-validation",
    "post-initial-investigation-through-final-local-validation",
}
KNOWN_SESSION_SOURCES = {
    "acp", "api", "cli", "cron", "dashboard", "desktop", "discord", "email",
    "gateway", "ide", "local", "matrix", "signal", "slack", "sms", "subagent",
    "teams", "telegram", "test", "webhook", "whatsapp",
}
KNOWN_COST_STATUSES = {"actual", "estimated", "included", "mixed", "partial", "unavailable"}
COUNTER_COLUMNS = (
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "reasoning_tokens",
    "api_call_count",
    "tool_call_count",
)
SESSION_COLUMNS = (
    "id",
    "parent_session_id",
    "source",
    "started_at",
    "ended_at",
    "model",
    "billing_provider",
    *COUNTER_COLUMNS,
    "actual_cost_usd",
    "estimated_cost_usd",
    "cost_source",
    "cost_status",
    "pricing_version",
)
COUNTER_KEYS = {
    "input_tokens": "inputTokens",
    "output_tokens": "outputTokens",
    "cache_read_tokens": "cacheReadTokens",
    "cache_write_tokens": "cacheWriteTokens",
    "reasoning_tokens": "reasoningTokens",
    "api_call_count": "apiCallCount",
    "tool_call_count": "toolCallCount",
}


class TrackerError(RuntimeError):
    """A fail-closed usage-tracking error safe to show to an operator."""


@contextmanager
def _persistent_lock(path: Path, timeout_seconds: float = 30.0):
    """Acquire an interprocess lock whose inode is never deleted."""
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    deadline = time.monotonic() + timeout_seconds
    locked = False
    try:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
            os.fsync(stream.fileno())
        while not locked:
            stream.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError as error:
                if time.monotonic() >= deadline:
                    raise TrackerError("Timed out waiting for the usage history lock") from error
                time.sleep(0.05)
        yield
    finally:
        if locked:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def _require_technical_string(value: Any, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not TECHNICAL_VALUE_PATTERN.fullmatch(value):
        raise TrackerError(f"Invalid {field}")
    return value


def _require_counter(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TrackerError(f"Invalid {field}")
    return value


def _require_epoch(value: Any, field: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TrackerError(f"Invalid {field}")
    try:
        converted = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise TrackerError(f"Invalid {field}") from error
    if not math.isfinite(converted) or converted < 0:
        raise TrackerError(f"Invalid {field}")
    return converted


def _require_cost(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TrackerError(f"Invalid {field}")
    try:
        converted = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise TrackerError(f"Invalid {field}") from error
    if not math.isfinite(converted) or converted < 0:
        raise TrackerError(f"Invalid {field}")
    return converted


def _validate_session(row: sqlite3.Row) -> dict[str, Any]:
    session = dict(row)
    for key in ("id", "source", "model", "billing_provider", "cost_source", "cost_status"):
        _require_technical_string(session[key], key)
    if session["source"] not in KNOWN_SESSION_SOURCES:
        raise TrackerError("Invalid source")
    if session["cost_status"] not in KNOWN_COST_STATUSES:
        raise TrackerError("Invalid cost_status")
    _require_technical_string(session["parent_session_id"], "parent_session_id", nullable=True)
    pricing = _require_technical_string(session["pricing_version"], "pricing_version", nullable=True)
    started_at = _require_epoch(session["started_at"], "started_at")
    ended_at = _require_epoch(session["ended_at"], "ended_at", nullable=True)
    if ended_at is not None and ended_at < started_at:
        raise TrackerError("Session ended before it started")
    for column in COUNTER_COLUMNS:
        _require_counter(session[column], column)
    actual = _require_cost(session["actual_cost_usd"], "actual_cost_usd")
    estimated = _require_cost(session["estimated_cost_usd"], "estimated_cost_usd")
    status = session["cost_status"]
    if status == "included" and (
        actual not in {None, 0.0} or estimated not in {None, 0.0} or pricing is not None
    ):
        raise TrackerError("Invalid Hermes cost facts")
    if status == "unavailable" and (actual is not None or estimated is not None or pricing is not None):
        raise TrackerError("Invalid Hermes cost facts")
    if status == "actual" and (actual is None or estimated is not None):
        raise TrackerError("Invalid Hermes cost facts")
    if status == "estimated" and (actual is not None or estimated is None or pricing is None):
        raise TrackerError("Invalid Hermes cost facts")
    if status in {"mixed", "partial"} and actual is None and estimated is None:
        raise TrackerError("Invalid Hermes cost facts")
    return session


def _read_session(state_database: Path, session_id: str) -> dict[str, Any]:
    _require_technical_string(session_id, "session_id")
    query = f"SELECT {', '.join(SESSION_COLUMNS)} FROM sessions WHERE id = ?"
    try:
        with closing(sqlite3.connect(state_database)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(query, (session_id,)).fetchone()
    except sqlite3.Error as error:
        raise TrackerError("Unable to read Hermes session usage") from error
    if row is None:
        raise TrackerError("Hermes session not found")
    return _validate_session(row)


def _snapshot_path(root: Path, work_id: str) -> Path:
    if not isinstance(work_id, str) or not WORK_ID_PATTERN.fullmatch(work_id):
        raise TrackerError("Invalid work_id")
    return root / ".ai-usage" / f"{work_id}.json"


def _active_work_for_session(root: Path, session_id: str) -> str | None:
    snapshot_directory = root / ".ai-usage"
    if not snapshot_directory.exists():
        return None
    for path in snapshot_directory.glob("*.json"):
        snapshot = _read_json(path)
        work_id = snapshot.get("workId")
        session = snapshot.get("session")
        if (
            not isinstance(work_id, str)
            or not WORK_ID_PATTERN.fullmatch(work_id)
            or not isinstance(session, dict)
            or "id" not in session
        ):
            raise TrackerError("Invalid active usage snapshot")
        snapshot_session_id = _require_technical_string(session["id"], "snapshot session id")
        if snapshot_session_id == session_id:
            return work_id
    return None


def _isoformat(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise TrackerError("captured_at must include a timezone")
    return value.astimezone(timezone.utc).isoformat()


def _write_exclusive_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as error:
        raise TrackerError("A starting snapshot already exists for this work_id") from error


def _start_measurement_unlocked(
    *,
    root: Path,
    state_database: Path,
    work_id: str,
    session_id: str,
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    """Capture an exclusive, sanitized starting snapshot."""
    timestamp = captured_at or datetime.now(timezone.utc)
    session = _read_session(Path(state_database), session_id)
    checkpoint = timestamp.timestamp()
    if checkpoint < session["started_at"]:
        raise TrackerError("Starting snapshot is before the Hermes session started")
    if session["ended_at"] is not None and checkpoint > session["ended_at"]:
        raise TrackerError("Starting snapshot is after the Hermes session ended")
    snapshot = {
        "schemaVersion": SCHEMA_VERSION,
        "workId": work_id,
        "measurementStatus": "started",
        "measurementBoundary": "development-through-final-local-validation",
        "capturedAtEpoch": timestamp.timestamp(),
        "capturedAt": _isoformat(timestamp),
        "collector": {"source": "hermes-state-db", "schemaVersion": 1},
        "session": {
            "id": session["id"],
            "source": session["source"],
            "sessionStartedAtEpoch": session["started_at"],
            "provider": session["billing_provider"],
            "model": session["model"],
            "costSource": session["cost_source"],
            "costStatus": session["cost_status"],
            "pricingVersion": session["pricing_version"],
            "actualCostUsd": session["actual_cost_usd"],
            "estimatedCostUsd": session["estimated_cost_usd"],
        },
        "counters": {COUNTER_KEYS[column]: session[column] for column in COUNTER_COLUMNS},
    }
    _write_exclusive_json(_snapshot_path(Path(root), work_id), snapshot)
    return snapshot


def start_measurement(
    *,
    root: Path,
    state_database: Path,
    work_id: str,
    session_id: str,
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    """Capture an exclusive snapshot after checking canonical history."""
    root = Path(root)
    snapshot_path = _snapshot_path(root, work_id)
    history_path = root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
    with _persistent_lock(snapshot_path.with_suffix(".lock")):
        with _persistent_lock(root / ".ai-usage" / "history.lock"):
            records = _read_history(history_path)
            if any(record["workId"] == work_id for record in records):
                raise TrackerError("work_id already exists in canonical usage history")
            active_work = _active_work_for_session(root, session_id)
            if active_work is not None:
                raise TrackerError(f"Session already has active work: {active_work}")
            return _start_measurement_unlocked(
                root=root,
                state_database=Path(state_database),
                work_id=work_id,
                session_id=session_id,
                captured_at=captured_at,
            )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TrackerError("Unable to read the starting snapshot") from error
    if not isinstance(value, dict):
        raise TrackerError("Invalid starting snapshot")
    return value


def _require_exact_keys(value: Any, expected: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise TrackerError(f"Invalid {field}")
    return value


def _parse_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise TrackerError(f"Invalid {field}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise TrackerError(f"Invalid {field}") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TrackerError(f"Invalid {field}")
    return parsed.astimezone(timezone.utc)


def _validate_counters(value: Any, field: str, *, include_total: bool = False) -> dict[str, int]:
    expected = set(COUNTER_KEYS.values())
    if include_total:
        expected.add("totalTokens")
    counters = _require_exact_keys(value, expected, field)
    for key in expected:
        _require_counter(counters[key], f"{field}.{key}")
    if include_total and counters["totalTokens"] != counters["inputTokens"] + counters["outputTokens"]:
        raise TrackerError(f"Invalid {field}.totalTokens")
    return counters


def _validate_cost(value: Any, field: str, *, allow_empty_partial: bool = False) -> dict[str, Any]:
    cost = _require_exact_keys(value, {"status", "actualUsd", "estimatedUsd", "pricingVersion"}, field)
    if cost["status"] not in {"actual", "estimated", "included", "mixed", "partial", "unavailable"}:
        raise TrackerError(f"Invalid {field}.status")
    actual = _require_cost(cost["actualUsd"], f"{field}.actualUsd")
    estimated = _require_cost(cost["estimatedUsd"], f"{field}.estimatedUsd")
    pricing = _require_technical_string(cost["pricingVersion"], f"{field}.pricingVersion", nullable=True)
    if cost["status"] in {"included", "unavailable"} and (actual is not None or estimated is not None or pricing is not None):
        raise TrackerError(f"Invalid {field}")
    if cost["status"] == "actual" and (actual is None or estimated is not None):
        raise TrackerError(f"Invalid {field}")
    if cost["status"] == "estimated" and (actual is not None or estimated is None or pricing is None):
        raise TrackerError(f"Invalid {field}")
    if cost["status"] == "mixed" and actual is None and estimated is None:
        raise TrackerError(f"Invalid {field}")
    if cost["status"] == "partial" and actual is None and estimated is None and not allow_empty_partial:
        raise TrackerError(f"Invalid {field}")
    return cost


def _validate_snapshot(value: dict[str, Any], work_id: str) -> dict[str, Any]:
    snapshot = _require_exact_keys(
        value,
        {
            "schemaVersion", "workId", "measurementStatus", "measurementBoundary",
            "capturedAtEpoch", "capturedAt", "collector", "session", "counters",
        },
        "starting snapshot",
    )
    if snapshot["schemaVersion"] != SCHEMA_VERSION or snapshot["workId"] != work_id:
        raise TrackerError("Invalid starting snapshot")
    if snapshot["measurementStatus"] != "started" or snapshot["measurementBoundary"] != "development-through-final-local-validation":
        raise TrackerError("Invalid starting snapshot")
    captured_epoch = _require_epoch(snapshot["capturedAtEpoch"], "capturedAtEpoch")
    captured_at = _parse_timestamp(snapshot["capturedAt"], "capturedAt")
    if abs(captured_at.timestamp() - captured_epoch) > 0.001:
        raise TrackerError("Invalid starting snapshot timestamp")
    collector = _require_exact_keys(snapshot["collector"], {"source", "schemaVersion"}, "snapshot collector")
    if collector != {"source": "hermes-state-db", "schemaVersion": 1}:
        raise TrackerError("Invalid snapshot collector")
    session = _require_exact_keys(
        snapshot["session"],
        {
            "id", "source", "sessionStartedAtEpoch", "provider", "model", "costSource",
            "costStatus", "pricingVersion", "actualCostUsd", "estimatedCostUsd",
        },
        "snapshot session",
    )
    for key in ("id", "source", "provider", "model", "costSource", "costStatus"):
        _require_technical_string(session[key], f"snapshot session.{key}")
    if session["source"] not in KNOWN_SESSION_SOURCES or session["costStatus"] not in KNOWN_COST_STATUSES:
        raise TrackerError("Invalid snapshot session source or cost status")
    pricing = _require_technical_string(session["pricingVersion"], "snapshot session.pricingVersion", nullable=True)
    session_started = _require_epoch(session["sessionStartedAtEpoch"], "snapshot session.sessionStartedAtEpoch")
    actual = _require_cost(session["actualCostUsd"], "snapshot session.actualCostUsd")
    estimated = _require_cost(session["estimatedCostUsd"], "snapshot session.estimatedCostUsd")
    status = session["costStatus"]
    if captured_epoch < session_started:
        raise TrackerError("Invalid starting snapshot timestamp")
    if status == "included" and (
        actual not in {None, 0.0} or estimated not in {None, 0.0} or pricing is not None
    ):
        raise TrackerError("Invalid snapshot cost facts")
    if status == "unavailable" and (actual is not None or estimated is not None or pricing is not None):
        raise TrackerError("Invalid snapshot cost facts")
    if status == "actual" and (actual is None or estimated is not None):
        raise TrackerError("Invalid snapshot cost facts")
    if status == "estimated" and (actual is not None or estimated is None or pricing is None):
        raise TrackerError("Invalid snapshot cost facts")
    if status in {"mixed", "partial"} and actual is None and estimated is None:
        raise TrackerError("Invalid snapshot cost facts")
    _validate_counters(snapshot["counters"], "snapshot counters")
    return snapshot


def _read_descendants(state_database: Path, parent: dict[str, Any]) -> list[dict[str, Any]]:
    query = f"SELECT {', '.join(SESSION_COLUMNS)} FROM sessions WHERE parent_session_id = ?"
    descendants: list[dict[str, Any]] = []
    frontier = [parent["id"]]
    seen = {parent["id"]}
    sessions_by_id = {parent["id"]: parent}
    try:
        with closing(sqlite3.connect(state_database)) as connection:
            connection.row_factory = sqlite3.Row
            while frontier:
                rows = connection.execute(query, (frontier.pop(0),)).fetchall()
                for row in rows:
                    session = _validate_session(row)
                    session_id = session["id"]
                    if session_id in seen:
                        raise TrackerError("Duplicate or cyclic delegated session")
                    direct_parent = sessions_by_id[session["parent_session_id"]]
                    if session["started_at"] < direct_parent["started_at"] or (
                        direct_parent["ended_at"] is not None
                        and (session["ended_at"] is None or session["ended_at"] > direct_parent["ended_at"])
                    ):
                        raise TrackerError("Delegated session is outside its parent session lifetime")
                    seen.add(session_id)
                    sessions_by_id[session_id] = session
                    descendants.append(session)
                    frontier.append(session_id)
    except sqlite3.Error as error:
        raise TrackerError("Unable to read delegated Hermes usage") from error
    return descendants


def _delta_counters(ending: dict[str, Any], starting: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for column, key in COUNTER_KEYS.items():
        start_value = _require_counter(starting[key], key)
        end_value = _require_counter(ending[column], column)
        if end_value < start_value:
            raise TrackerError(f"Counter moved backward: {key}")
        result[key] = end_value - start_value
    return result


def _full_counters(session: dict[str, Any]) -> dict[str, int]:
    return {key: _require_counter(session[column], column) for column, key in COUNTER_KEYS.items()}


def _sum_counters(counter_sets: list[dict[str, int]]) -> dict[str, int]:
    totals = {key: 0 for key in COUNTER_KEYS.values()}
    for counters in counter_sets:
        for key in totals:
            totals[key] += counters[key]
    totals["totalTokens"] = totals["inputTokens"] + totals["outputTokens"]
    return totals


def _included_cost() -> dict[str, Any]:
    return {
        "status": "included",
        "actualUsd": None,
        "estimatedUsd": None,
        "pricingVersion": None,
    }


def _session_cost(session: dict[str, Any]) -> dict[str, Any]:
    status = session["cost_status"]
    actual = session["actual_cost_usd"]
    estimated = session["estimated_cost_usd"]
    pricing = session["pricing_version"]
    if status == "included":
        return _included_cost()
    if status == "unavailable":
        return {"status": status, "actualUsd": None, "estimatedUsd": None, "pricingVersion": None}
    if status == "actual" and actual is not None:
        return {"status": status, "actualUsd": actual, "estimatedUsd": None, "pricingVersion": pricing}
    if status == "estimated" and estimated is not None and pricing is not None:
        return {"status": status, "actualUsd": None, "estimatedUsd": estimated, "pricingVersion": pricing}
    if status in {"mixed", "partial"} and (actual is not None or estimated is not None):
        return {"status": status, "actualUsd": actual, "estimatedUsd": estimated, "pricingVersion": pricing}
    raise TrackerError("Invalid Hermes cost facts")


def _main_cost(ending: dict[str, Any], snapshot_session: dict[str, Any]) -> dict[str, Any]:
    if ending["cost_status"] != snapshot_session.get("costStatus"):
        raise TrackerError("Hermes cost status changed during measurement")
    status = ending["cost_status"]
    if status in {"included", "unavailable"}:
        return _session_cost(ending)
    if ending["pricing_version"] != snapshot_session.get("pricingVersion"):
        raise TrackerError("Hermes pricing version changed during measurement")

    def delta(field: str, snapshot_field: str) -> float | None:
        current = _require_cost(ending[field], field)
        starting = _require_cost(snapshot_session.get(snapshot_field), snapshot_field)
        if current is None and starting is None:
            return None
        if current is None or starting is None or current < starting:
            raise TrackerError(f"Cost moved backward or became unavailable: {field}")
        return current - starting

    actual = delta("actual_cost_usd", "actualCostUsd")
    estimated = delta("estimated_cost_usd", "estimatedCostUsd")
    cost = {
        "status": status,
        "actualUsd": actual if status in {"actual", "mixed", "partial"} else None,
        "estimatedUsd": estimated if status in {"estimated", "mixed", "partial"} else None,
        "pricingVersion": ending["pricing_version"],
    }
    return _validate_cost(cost, "main cost")


def _aggregate_costs(costs: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {cost["status"] for cost in costs}
    actual_values = [cost["actualUsd"] for cost in costs if cost["actualUsd"] is not None]
    estimated_values = [cost["estimatedUsd"] for cost in costs if cost["estimatedUsd"] is not None]
    pricing_versions = {cost["pricingVersion"] for cost in costs if cost["pricingVersion"] is not None}
    actual = math.fsum(actual_values) if actual_values else None
    estimated = math.fsum(estimated_values) if estimated_values else None
    pricing = next(iter(pricing_versions)) if len(pricing_versions) == 1 else None
    if statuses == {"included"}:
        return _included_cost()
    if statuses == {"unavailable"}:
        return {"status": "unavailable", "actualUsd": None, "estimatedUsd": None, "pricingVersion": None}
    if statuses == {"actual"}:
        return {"status": "actual", "actualUsd": actual, "estimatedUsd": None, "pricingVersion": pricing}
    if statuses == {"estimated"} and pricing is not None:
        return {"status": "estimated", "actualUsd": None, "estimatedUsd": estimated, "pricingVersion": pricing}
    status = "partial" if statuses & {"unavailable", "partial"} else "mixed"
    return _validate_cost(
        {"status": status, "actualUsd": actual, "estimatedUsd": estimated, "pricingVersion": pricing},
        "aggregate cost",
        allow_empty_partial=True,
    )


def _validate_delivery_metadata(
    feature_name: str,
    pr_number: int | None,
    pr_url: str | None,
    commit_sha: str | None,
) -> dict[str, Any]:
    if not isinstance(feature_name, str) or not FEATURE_NAME_PATTERN.fullmatch(feature_name):
        raise TrackerError("Invalid feature_name")
    if pr_number is not None and (isinstance(pr_number, bool) or not isinstance(pr_number, int) or pr_number <= 0):
        raise TrackerError("Invalid pr_number")
    if pr_url is not None:
        _require_technical_string(pr_url, "pr_url")
        if pr_number is None or not pr_url.endswith(f"/pull/{pr_number}"):
            raise TrackerError("PR URL does not match pr_number")
    if commit_sha is not None and (not isinstance(commit_sha, str) or not COMMIT_PATTERN.fullmatch(commit_sha)):
        raise TrackerError("Invalid commit_sha")
    return {"number": pr_number, "url": pr_url, "commitSha": commit_sha}


def _validate_agent(value: Any, role: str) -> dict[str, Any]:
    expected = {"sessionId", "role", "counters", "cost"}
    if role == "subagent":
        expected.add("parentSessionId")
    agent = _require_exact_keys(value, expected, f"{role} agent")
    _require_technical_string(agent["sessionId"], f"{role} sessionId")
    if role == "subagent":
        _require_technical_string(agent["parentSessionId"], "subagent parentSessionId")
    if agent["role"] != role:
        raise TrackerError(f"Invalid {role} role")
    _validate_counters(agent["counters"], f"{role} counters")
    _validate_cost(agent["cost"], f"{role} cost")
    return agent


def _validate_record(value: Any) -> dict[str, Any]:
    required_keys = {
        "schemaVersion", "workId", "featureName", "measurementStatus",
        "measurementBoundary", "provider", "model", "startedAt", "finishedAt",
        "delivery", "mainAgent", "delegatedAgents", "totals", "cost",
    }
    if not isinstance(value, dict) or set(value) not in {frozenset(required_keys), frozenset(required_keys | {"notes"})}:
        raise TrackerError("Invalid usage record")
    record = dict(value)
    record.setdefault("notes", "")
    if record["schemaVersion"] != SCHEMA_VERSION or record["measurementStatus"] != "complete":
        raise TrackerError("Invalid usage record")
    if not isinstance(record["workId"], str) or not WORK_ID_PATTERN.fullmatch(record["workId"]):
        raise TrackerError("Invalid usage record workId")
    if not isinstance(record["featureName"], str) or not FEATURE_NAME_PATTERN.fullmatch(record["featureName"]):
        raise TrackerError("Invalid usage record featureName")
    if record["measurementBoundary"] not in MEASUREMENT_BOUNDARIES:
        raise TrackerError("Invalid usage record boundary")
    if record["notes"] != "" and (
        not isinstance(record["notes"], str) or not NOTE_PATTERN.fullmatch(record["notes"])
    ):
        raise TrackerError("Invalid usage record notes")
    _require_technical_string(record["provider"], "usage record provider")
    _require_technical_string(record["model"], "usage record model")
    started_at = _parse_timestamp(record["startedAt"], "usage record startedAt")
    finished_at = _parse_timestamp(record["finishedAt"], "usage record finishedAt")
    if finished_at < started_at:
        raise TrackerError("Invalid usage record time range")
    delivery = _require_exact_keys(record["delivery"], {"number", "url", "commitSha"}, "usage record delivery")
    _validate_delivery_metadata(record["featureName"], delivery["number"], delivery["url"], delivery["commitSha"])
    main_agent = _validate_agent(record["mainAgent"], "main")
    if not isinstance(record["delegatedAgents"], list):
        raise TrackerError("Invalid delegatedAgents")
    delegated_agents = [_validate_agent(agent, "subagent") for agent in record["delegatedAgents"]]
    session_ids = [main_agent["sessionId"], *(agent["sessionId"] for agent in delegated_agents)]
    if len(session_ids) != len(set(session_ids)):
        raise TrackerError("Duplicate session in usage record")
    delegated_by_id = {agent["sessionId"]: agent for agent in delegated_agents}
    for agent in delegated_agents:
        current = agent
        ancestors: set[str] = set()
        while current["parentSessionId"] != main_agent["sessionId"]:
            parent_id = current["parentSessionId"]
            if parent_id in ancestors or parent_id not in delegated_by_id:
                raise TrackerError("Disconnected or cyclic delegated session")
            ancestors.add(parent_id)
            current = delegated_by_id[parent_id]
    totals = _validate_counters(record["totals"], "usage totals", include_total=True)
    calculated = _sum_counters([main_agent["counters"], *(agent["counters"] for agent in delegated_agents)])
    if totals != calculated:
        raise TrackerError("Usage totals do not reconcile")
    aggregate_cost = _validate_cost(record["cost"], "usage cost", allow_empty_partial=True)
    calculated_cost = _aggregate_costs([main_agent["cost"], *(agent["cost"] for agent in delegated_agents)])
    if aggregate_cost != calculated_cost:
        raise TrackerError("Usage costs do not reconcile")
    return record


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _render_csv(records: list[dict[str, Any]]) -> str:
    header = [
        "feature_id", "feature_name", "measurement_status", "measurement_boundary",
        "provider", "model", "started_at", "finished_at", "input_tokens",
        "cache_read_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens",
        "total_tokens", "cost_status", "actual_cost_usd", "estimated_cost_usd",
        "pricing_version", "notes",
    ]
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(header)
    for record in records:
        totals = record["totals"]
        cost = record["cost"]
        writer.writerow([
            record["workId"], record["featureName"], record["measurementStatus"],
            record["measurementBoundary"], record["provider"], record["model"],
            record["startedAt"], record["finishedAt"], totals["inputTokens"],
            totals["cacheReadTokens"], totals["cacheWriteTokens"], totals["outputTokens"],
            totals["reasoningTokens"], totals["totalTokens"], cost["status"],
            "" if cost["actualUsd"] is None else cost["actualUsd"],
            "" if cost["estimatedUsd"] is None else cost["estimatedUsd"],
            "" if cost["pricingVersion"] is None else cost["pricingVersion"],
            record["notes"],
        ])
    return output.getvalue()


def _validate_history_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validated = [_validate_record(record) for record in records]
    work_ids = [record["workId"] for record in validated]
    if len(work_ids) != len(set(work_ids)):
        raise TrackerError("Duplicate work_id in canonical usage history")
    intervals_by_session: dict[str, list[tuple[datetime, datetime]]] = {}
    for record in validated:
        started_at = _parse_timestamp(record["startedAt"], "startedAt")
        finished_at = _parse_timestamp(record["finishedAt"], "finishedAt")
        session_ids = [
            record["mainAgent"]["sessionId"],
            *(agent["sessionId"] for agent in record["delegatedAgents"]),
        ]
        for session_id in session_ids:
            intervals = intervals_by_session.setdefault(session_id, [])
            if any(started_at < previous_end and previous_start < finished_at for previous_start, previous_end in intervals):
                raise TrackerError("Overlapping measurements for the same session")
            intervals.append((started_at, finished_at))
    return validated


def _read_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return _validate_history_records([json.loads(line) for line in lines if line.strip()])
    except (OSError, UnicodeError, json.JSONDecodeError, TrackerError) as error:
        raise TrackerError("Invalid canonical usage history") from error


def _finish_measurement_unlocked(
    *,
    root: Path,
    state_database: Path,
    work_id: str,
    feature_name: str,
    pr_number: int | None = None,
    pr_url: str | None = None,
    commit_sha: str | None = None,
    finished_at: datetime | None = None,
) -> dict[str, Any]:
    """Finalize a measurement and atomically persist canonical and CSV views."""
    root = Path(root)
    snapshot_path = _snapshot_path(root, work_id)
    snapshot = _validate_snapshot(_read_json(snapshot_path), work_id)
    delivery = _validate_delivery_metadata(feature_name, pr_number, pr_url, commit_sha)
    history_path = root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
    records = _read_history(history_path)
    existing = next((record for record in records if record["workId"] == work_id), None)
    if existing is not None:
        if (
            existing["featureName"] != feature_name
            or existing["delivery"] != delivery
            or existing["startedAt"] != snapshot["capturedAt"]
            or existing["mainAgent"]["sessionId"] != snapshot["session"]["id"]
        ):
            raise TrackerError("Conflicting work_id in canonical usage history")
        _atomic_write(history_path.with_suffix(".csv"), _render_csv(records))
        snapshot_path.unlink()
        return existing
    ending = _read_session(Path(state_database), snapshot["session"]["id"])
    if ending["billing_provider"] != snapshot["session"]["provider"] or ending["model"] != snapshot["session"]["model"]:
        raise TrackerError("Hermes provider or model changed during measurement")
    if (
        ending["source"] != snapshot["session"]["source"]
        or ending["started_at"] != snapshot["session"]["sessionStartedAtEpoch"]
        or ending["cost_source"] != snapshot["session"]["costSource"]
    ):
        raise TrackerError("Starting snapshot does not match the live Hermes session")
    main_counters = _delta_counters(ending, snapshot["counters"])
    checkpoint = _require_epoch(snapshot["capturedAtEpoch"], "capturedAtEpoch")
    timestamp = finished_at or datetime.now(timezone.utc)
    finished_at_value = _isoformat(timestamp)
    parsed_finished_at = _parse_timestamp(finished_at_value, "finishedAt")
    if parsed_finished_at < _parse_timestamp(snapshot["capturedAt"], "capturedAt"):
        raise TrackerError("finished_at is before the starting snapshot")
    finished_epoch = parsed_finished_at.timestamp()
    if ending["ended_at"] is not None and not checkpoint <= ending["ended_at"] <= finished_epoch:
        raise TrackerError("Hermes main session is outside the measurement boundary")
    delegated_agents = []
    for child in _read_descendants(Path(state_database), ending):
        if child["started_at"] < checkpoint:
            if child["ended_at"] is None or child["ended_at"] >= checkpoint:
                raise TrackerError("Delegated session overlaps the measurement boundary")
            continue
        if child["billing_provider"] != ending["billing_provider"] or child["model"] != ending["model"]:
            raise TrackerError("Delegated session provider or model drift")
        if child["ended_at"] is None:
            raise TrackerError("Delegated session is still active")
        if child["ended_at"] > finished_epoch:
            raise TrackerError("Delegated session ends after the measurement")
        delegated_agents.append({
            "sessionId": child["id"],
            "parentSessionId": child["parent_session_id"],
            "role": "subagent",
            "counters": _full_counters(child),
            "cost": _session_cost(child),
        })
    main_agent = {
        "sessionId": ending["id"],
        "role": "main",
        "counters": main_counters,
        "cost": _main_cost(ending, snapshot["session"]),
    }
    totals = _sum_counters([main_counters, *(agent["counters"] for agent in delegated_agents)])
    record = {
        "schemaVersion": SCHEMA_VERSION,
        "workId": work_id,
        "featureName": feature_name,
        "measurementStatus": "complete",
        "measurementBoundary": snapshot["measurementBoundary"],
        "provider": ending["billing_provider"],
        "model": ending["model"],
        "startedAt": snapshot["capturedAt"],
        "finishedAt": finished_at_value,
        "delivery": delivery,
        "mainAgent": main_agent,
        "delegatedAgents": delegated_agents,
        "totals": totals,
        "cost": _aggregate_costs([main_agent["cost"], *(agent["cost"] for agent in delegated_agents)]),
        "notes": f"Main-session delta plus {len(delegated_agents)} linked subagents.",
    }
    record = _validate_record(record)
    records.append(record)
    _validate_history_records(records)
    _atomic_write(history_path, "".join(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n" for value in records))
    _atomic_write(history_path.with_suffix(".csv"), _render_csv(records))
    snapshot_path.unlink()
    return record


def finish_measurement(
    *,
    root: Path,
    state_database: Path,
    work_id: str,
    feature_name: str,
    pr_number: int | None = None,
    pr_url: str | None = None,
    commit_sha: str | None = None,
    finished_at: datetime | None = None,
) -> dict[str, Any]:
    """Serialize snapshot consumption and history persistence across processes."""
    root = Path(root)
    snapshot_path = _snapshot_path(root, work_id)
    history_path = root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
    delivery = _validate_delivery_metadata(feature_name, pr_number, pr_url, commit_sha)
    with _persistent_lock(snapshot_path.with_suffix(".lock")):
        with _persistent_lock(root / ".ai-usage" / "history.lock"):
            records = _read_history(history_path)
            existing = next((record for record in records if record["workId"] == work_id), None)
            if not snapshot_path.exists():
                if existing is None:
                    raise TrackerError("Starting snapshot not found")
                if existing["featureName"] != feature_name or existing["delivery"] != delivery:
                    raise TrackerError("Conflicting work_id in canonical usage history")
                _atomic_write(history_path.with_suffix(".csv"), _render_csv(records))
                return existing
            return _finish_measurement_unlocked(
                root=root,
                state_database=Path(state_database),
                work_id=work_id,
                feature_name=feature_name,
                pr_number=pr_number,
                pr_url=pr_url,
                commit_sha=commit_sha,
                finished_at=finished_at,
            )


def regenerate_report(*, root: Path) -> dict[str, int]:
    """Validate canonical history and atomically regenerate the CSV view."""
    root = Path(root)
    history_path = root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
    with _persistent_lock(root / ".ai-usage" / "history.lock"):
        records = _read_history(history_path)
        _atomic_write(history_path.with_suffix(".csv"), _render_csv(records))
    return {"records": len(records)}


def _discover_state_database(explicit_path: str | None) -> Path:
    if explicit_path:
        return Path(explicit_path)
    environment_path = os.environ.get("HERMES_STATE_DB")
    if environment_path:
        return Path(environment_path)
    try:
        completed = subprocess.run(
            ["hermes", "config", "path"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise TrackerError("Unable to locate the Hermes state database; use --state-db") from error
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise TrackerError("Unexpected output from hermes config path; use --state-db")
    config_path = Path(lines[0])
    state_database = config_path.with_name("state.db")
    if not state_database.is_file():
        raise TrackerError("Hermes state database not found; use --state-db")
    return state_database


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--state-db", help="Explicit Hermes state.db path")
    commands = parser.add_subparsers(dest="command", required=True)
    start_parser = commands.add_parser("start", help="Capture a starting usage snapshot")
    start_parser.add_argument("work_id")
    start_parser.add_argument("--session-id", required=True)
    finish_parser = commands.add_parser("finish", help="Finalize and persist a usage record")
    finish_parser.add_argument("work_id")
    finish_parser.add_argument("--feature-name", required=True)
    finish_parser.add_argument("--pr-number", type=int)
    finish_parser.add_argument("--pr-url")
    finish_parser.add_argument("--commit-sha")
    commands.add_parser("report", help="Validate JSONL history and regenerate the CSV view")
    return parser


def main(arguments: list[str] | None = None) -> int:
    parser = _build_parser()
    options = parser.parse_args(arguments)
    try:
        root = Path(options.root).resolve()
        if options.command == "report":
            result = regenerate_report(root=root)
        elif options.command == "start":
            state_database = _discover_state_database(options.state_db)
            result = start_measurement(
                root=root,
                state_database=state_database,
                work_id=options.work_id,
                session_id=options.session_id,
            )
        else:
            state_database = _discover_state_database(options.state_db)
            result = finish_measurement(
                root=root,
                state_database=state_database,
                work_id=options.work_id,
                feature_name=options.feature_name,
                pr_number=options.pr_number,
                pr_url=options.pr_url,
                commit_sha=options.commit_sha,
            )
    except TrackerError as error:
        print(f"ai-usage: error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
