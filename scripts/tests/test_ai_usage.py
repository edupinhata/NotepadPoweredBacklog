import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIRECTORY))

import ai_usage


SESSION_COLUMNS = """
    id TEXT PRIMARY KEY,
    parent_session_id TEXT,
    source TEXT NOT NULL,
    started_at REAL NOT NULL,
    ended_at REAL,
    model TEXT NOT NULL,
    billing_provider TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cache_read_tokens INTEGER NOT NULL,
    cache_write_tokens INTEGER NOT NULL,
    reasoning_tokens INTEGER NOT NULL,
    api_call_count INTEGER NOT NULL,
    tool_call_count INTEGER NOT NULL,
    actual_cost_usd REAL,
    estimated_cost_usd REAL,
    cost_source TEXT NOT NULL,
    cost_status TEXT NOT NULL,
    pricing_version TEXT
"""


class AiUsageTrackerTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.state_database = self.root / "state.db"
        with closing(sqlite3.connect(self.state_database)) as connection:
            connection.execute(f"CREATE TABLE sessions ({SESSION_COLUMNS})")
            self.insert_session(connection, session_id="parent")
            connection.commit()

    def tearDown(self):
        self.temporary_directory.cleanup()

    @staticmethod
    def insert_session(
        connection,
        *,
        session_id,
        parent_session_id=None,
        source="telegram",
        started_at=100.0,
        ended_at=None,
        model="test-model",
        provider="test-provider",
        input_tokens=100,
        output_tokens=20,
        cache_read_tokens=30,
        cache_write_tokens=0,
        reasoning_tokens=5,
        api_call_count=2,
        tool_call_count=3,
        actual_cost_usd=None,
        estimated_cost_usd=0.0,
        cost_source="none",
        cost_status="included",
        pricing_version=None,
    ):
        connection.execute(
            """
            INSERT INTO sessions (
                id, parent_session_id, source, started_at, ended_at, model,
                billing_provider, input_tokens, output_tokens,
                cache_read_tokens, cache_write_tokens, reasoning_tokens,
                api_call_count, tool_call_count, actual_cost_usd,
                estimated_cost_usd, cost_source, cost_status, pricing_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                parent_session_id,
                source,
                started_at,
                ended_at,
                model,
                provider,
                input_tokens,
                output_tokens,
                cache_read_tokens,
                cache_write_tokens,
                reasoning_tokens,
                api_call_count,
                tool_call_count,
                actual_cost_usd,
                estimated_cost_usd,
                cost_source,
                cost_status,
                pricing_version,
            ),
        )

    def test_start_creates_sanitized_snapshot(self):
        captured_at = datetime(2026, 8, 29, 4, 0, tzinfo=timezone.utc)

        snapshot = ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="parser-hardening",
            session_id="parent",
            captured_at=captured_at,
        )

        snapshot_path = self.root / ".ai-usage" / "parser-hardening.json"
        self.assertTrue(snapshot_path.exists())
        self.assertEqual("parser-hardening", snapshot["workId"])
        self.assertEqual("parent", snapshot["session"]["id"])
        self.assertEqual(100, snapshot["counters"]["inputTokens"])
        self.assertNotIn("messages", json.dumps(snapshot))
        self.assertEqual(snapshot, json.loads(snapshot_path.read_text(encoding="utf-8")))

    def test_start_rejects_unknown_session_source(self):
        with closing(sqlite3.connect(self.state_database)) as connection:
            connection.execute("UPDATE sessions SET source = 'future-platform' WHERE id = 'parent'")
            connection.commit()

        with self.assertRaisesRegex(ai_usage.TrackerError, "source"):
            ai_usage.start_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="unknown-source",
                session_id="parent",
                captured_at=datetime.fromtimestamp(150, timezone.utc),
            )

    def test_start_rejects_nonzero_cost_for_included_session(self):
        with closing(sqlite3.connect(self.state_database)) as connection:
            connection.execute("UPDATE sessions SET actual_cost_usd = 9.5 WHERE id = 'parent'")
            connection.commit()

        with self.assertRaisesRegex(ai_usage.TrackerError, "cost facts"):
            ai_usage.start_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="contradictory-included-cost",
                session_id="parent",
                captured_at=datetime.fromtimestamp(150, timezone.utc),
            )

    def test_start_rejects_snapshot_before_session_started(self):
        with self.assertRaisesRegex(ai_usage.TrackerError, "before the Hermes session started"):
            ai_usage.start_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="before-session",
                session_id="parent",
                captured_at=datetime.fromtimestamp(50, timezone.utc),
            )

    def test_finish_records_parent_delta_and_completed_descendant_once(self):
        started_at = datetime.fromtimestamp(150, timezone.utc)
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="parser-hardening",
            session_id="parent",
            captured_at=started_at,
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            connection.execute(
                """
                UPDATE sessions
                SET input_tokens = 150, output_tokens = 30,
                    cache_read_tokens = 50, reasoning_tokens = 8,
                    api_call_count = 4, tool_call_count = 7
                WHERE id = 'parent'
                """
            )
            self.insert_session(
                connection,
                session_id="child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=170,
                input_tokens=40,
                output_tokens=10,
                cache_read_tokens=15,
                reasoning_tokens=2,
                api_call_count=1,
                tool_call_count=2,
            )
            connection.commit()

        record = ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="parser-hardening",
            feature_name="Parser hardening",
            pr_number=3,
            pr_url="https://github.com/example/project/pull/3",
            commit_sha="a" * 40,
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )

        self.assertEqual(50, record["mainAgent"]["counters"]["inputTokens"])
        self.assertEqual(40, record["delegatedAgents"][0]["counters"]["inputTokens"])
        self.assertEqual(90, record["totals"]["inputTokens"])
        self.assertEqual(110, record["totals"]["totalTokens"])
        self.assertEqual("included", record["cost"]["status"])
        self.assertIsNone(record["cost"]["actualUsd"])
        history_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
        persisted = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([record], persisted)
        self.assertFalse((self.root / ".ai-usage" / "parser-hardening.json").exists())
        csv_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.csv"
        self.assertIn("parser-hardening", csv_path.read_text(encoding="utf-8"))

    def test_finish_rejects_tampered_snapshot_and_preserves_it(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="tampered-snapshot",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        snapshot_path = self.root / ".ai-usage" / "tampered-snapshot.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["unexpected"] = "unsafe"
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

        with self.assertRaisesRegex(ai_usage.TrackerError, "Invalid starting snapshot"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="tampered-snapshot",
                feature_name="Tampered snapshot",
            )

        self.assertTrue(snapshot_path.exists())
        self.assertFalse((self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl").exists())

    def test_finish_rejects_semantically_tampered_snapshot(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="semantic-tamper",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        snapshot_path = self.root / ".ai-usage" / "semantic-tamper.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["session"]["sessionStartedAtEpoch"] = 999999
        snapshot["session"]["source"] = "slack"
        snapshot["session"]["costSource"] = "fabricated"
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

        with self.assertRaisesRegex(ai_usage.TrackerError, "snapshot"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="semantic-tamper",
                feature_name="Semantic tamper",
            )

        self.assertTrue(snapshot_path.exists())

    def test_finish_rejects_contradictory_snapshot_cost_facts(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="snapshot-cost-tamper",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        snapshot_path = self.root / ".ai-usage" / "snapshot-cost-tamper.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["session"]["actualCostUsd"] = 9.5
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

        with self.assertRaisesRegex(ai_usage.TrackerError, "Invalid snapshot cost facts"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="snapshot-cost-tamper",
                feature_name="Snapshot cost tamper",
            )

        self.assertTrue(snapshot_path.exists())

    def test_finish_rejects_active_descendant_and_preserves_snapshot(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="active-child",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            self.insert_session(
                connection,
                session_id="child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=None,
            )
            connection.commit()

        with self.assertRaisesRegex(ai_usage.TrackerError, "still active"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="active-child",
                feature_name="Active child",
            )

        self.assertTrue((self.root / ".ai-usage" / "active-child.json").exists())

    def test_finish_rejects_descendant_ending_before_it_started(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="backward-child-time",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            self.insert_session(
                connection,
                session_id="child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=155,
            )
            connection.commit()

        with self.assertRaisesRegex(ai_usage.TrackerError, "ended before it started"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="backward-child-time",
                feature_name="Backward child time",
            )

    def test_finish_rejects_descendant_ending_after_measurement(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="child-after-finish",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            self.insert_session(
                connection,
                session_id="child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=190,
            )
            connection.commit()

        with self.assertRaisesRegex(ai_usage.TrackerError, "ends after the measurement"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="child-after-finish",
                feature_name="Child after finish",
                finished_at=datetime.fromtimestamp(180, timezone.utc),
            )

    def test_finish_rejects_main_session_outside_measurement_boundary(self):
        for work_id, ended_at in (("main-before-start", 140), ("main-after-finish", 190)):
            with self.subTest(ended_at=ended_at):
                ai_usage.start_measurement(
                    root=self.root,
                    state_database=self.state_database,
                    work_id=work_id,
                    session_id="parent",
                    captured_at=datetime.fromtimestamp(150, timezone.utc),
                )
                with closing(sqlite3.connect(self.state_database)) as connection:
                    connection.execute("UPDATE sessions SET ended_at = ? WHERE id = 'parent'", (ended_at,))
                    connection.commit()

                try:
                    with self.assertRaisesRegex(ai_usage.TrackerError, "main session.*measurement boundary"):
                        ai_usage.finish_measurement(
                            root=self.root,
                            state_database=self.state_database,
                            work_id=work_id,
                            feature_name="Main session boundary",
                            finished_at=datetime.fromtimestamp(180, timezone.utc),
                        )
                finally:
                    (self.root / ".ai-usage" / f"{work_id}.json").unlink(missing_ok=True)
                    with closing(sqlite3.connect(self.state_database)) as connection:
                        connection.execute("UPDATE sessions SET ended_at = NULL WHERE id = 'parent'")
                        connection.commit()

    def test_finish_rejects_descendant_outside_direct_parent_lifetime(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="impossible-descendant-lifetime",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            self.insert_session(
                connection,
                session_id="child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=170,
            )
            self.insert_session(
                connection,
                session_id="grandchild",
                parent_session_id="child",
                source="subagent",
                started_at=155,
                ended_at=165,
            )
            connection.commit()

        with self.assertRaisesRegex(ai_usage.TrackerError, "outside its parent session lifetime"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="impossible-descendant-lifetime",
                feature_name="Impossible descendant lifetime",
                finished_at=datetime.fromtimestamp(180, timezone.utc),
            )

    def test_finish_rejects_descendant_provider_or_model_drift(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="child-drift",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            self.insert_session(
                connection,
                session_id="child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=170,
                model="other-model",
                provider="other-provider",
            )
            connection.commit()

        with self.assertRaisesRegex(ai_usage.TrackerError, "provider or model drift"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="child-drift",
                feature_name="Child drift",
            )

    def test_finish_rejects_backward_parent_counter(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="backward-counter",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            connection.execute("UPDATE sessions SET input_tokens = 99 WHERE id = 'parent'")
            connection.commit()

        with self.assertRaisesRegex(ai_usage.TrackerError, "moved backward"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="backward-counter",
                feature_name="Backward counter",
            )

    def test_finish_rejects_timestamp_before_start_and_preserves_snapshot(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="backward-time",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )

        with self.assertRaisesRegex(ai_usage.TrackerError, "before the starting snapshot"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="backward-time",
                feature_name="Backward time",
                finished_at=datetime.fromtimestamp(140, timezone.utc),
            )

        self.assertTrue((self.root / ".ai-usage" / "backward-time.json").exists())

    def test_finish_fails_closed_on_malformed_history(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="malformed-history",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        history_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text('{"not":"a valid record"}\n', encoding="utf-8")

        with self.assertRaisesRegex(ai_usage.TrackerError, "Invalid canonical usage history"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="malformed-history",
                feature_name="Malformed history",
            )

        self.assertTrue((self.root / ".ai-usage" / "malformed-history.json").exists())

    def test_report_rejects_aggregate_cost_that_does_not_reconcile(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="contradictory-cost",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="contradictory-cost",
            feature_name="Contradictory cost",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )
        history_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
        record = json.loads(history_path.read_text(encoding="utf-8"))
        record["cost"]["status"] = "unavailable"
        history_path.write_text(json.dumps(record, separators=(",", ":")) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ai_usage.TrackerError, "Invalid canonical usage history"):
            ai_usage.regenerate_report(root=self.root)

    def test_report_rejects_disconnected_delegated_agent(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="disconnected-agent",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            self.insert_session(
                connection,
                session_id="child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=170,
            )
            connection.commit()
        ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="disconnected-agent",
            feature_name="Disconnected agent",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )
        history_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
        record = json.loads(history_path.read_text(encoding="utf-8"))
        record["delegatedAgents"][0]["parentSessionId"] = "missing-parent"
        history_path.write_text(json.dumps(record, separators=(",", ":")) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ai_usage.TrackerError, "Invalid canonical usage history"):
            ai_usage.regenerate_report(root=self.root)

    def test_report_rejects_overlapping_records_for_same_session(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="first-work",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="first-work",
            feature_name="First work",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )
        history_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
        first = json.loads(history_path.read_text(encoding="utf-8"))
        overlapping = dict(first)
        overlapping["workId"] = "overlapping-work"
        history_path.write_text(
            "\n".join(json.dumps(record, separators=(",", ":")) for record in (first, overlapping)) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ai_usage.TrackerError, "Invalid canonical usage history"):
            ai_usage.regenerate_report(root=self.root)

    def test_finish_rejects_candidate_that_overlaps_canonical_history(self):
        with closing(sqlite3.connect(self.state_database)) as connection:
            self.insert_session(
                connection,
                session_id="child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=170,
            )
            connection.commit()
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="child-work",
            session_id="child",
            captured_at=datetime.fromtimestamp(160, timezone.utc),
        )
        ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="child-work",
            feature_name="Child work",
            finished_at=datetime.fromtimestamp(170, timezone.utc),
        )
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="parent-work",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )

        with self.assertRaisesRegex(ai_usage.TrackerError, "Overlapping measurements"):
            ai_usage.finish_measurement(
                root=self.root,
                state_database=self.state_database,
                work_id="parent-work",
                feature_name="Parent work",
                finished_at=datetime.fromtimestamp(180, timezone.utc),
            )

        history_lines = (self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertEqual(1, len(history_lines))
        self.assertTrue((self.root / ".ai-usage" / "parent-work.json").exists())

    def test_finish_preserves_partial_cost_without_numeric_amount(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="partial-without-amount",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            self.insert_session(
                connection,
                session_id="unavailable-child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=170,
                estimated_cost_usd=None,
                cost_status="unavailable",
            )
            connection.commit()

        record = ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="partial-without-amount",
            feature_name="Partial without amount",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )

        self.assertEqual("partial", record["cost"]["status"])
        self.assertIsNone(record["cost"]["actualUsd"])
        self.assertIsNone(record["cost"]["estimatedUsd"])

    def test_aggregate_preserves_partial_component_status(self):
        partial = {"status": "partial", "actualUsd": 1.0, "estimatedUsd": None, "pricingVersion": None}
        included = {"status": "included", "actualUsd": None, "estimatedUsd": None, "pricingVersion": None}

        aggregate = ai_usage._aggregate_costs([partial, included])

        self.assertEqual("partial", aggregate["status"])

    def test_idempotent_finish_repairs_csv_and_consumes_leftover_snapshot(self):
        started_at = datetime.fromtimestamp(150, timezone.utc)
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="idempotent-finish",
            session_id="parent",
            captured_at=started_at,
        )
        record = ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="idempotent-finish",
            feature_name="Idempotent finish",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )
        snapshot_path = self.root / ".ai-usage" / "idempotent-finish.json"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_text(
            json.dumps({
                "schemaVersion": 1,
                "workId": "idempotent-finish",
                "measurementStatus": "started",
                "measurementBoundary": "development-through-final-local-validation",
                "capturedAtEpoch": 150,
                "capturedAt": started_at.isoformat(),
                "collector": {"source": "hermes-state-db", "schemaVersion": 1},
                "session": {
                    "id": "parent", "source": "telegram", "sessionStartedAtEpoch": 100,
                    "provider": "test-provider", "model": "test-model", "costSource": "none",
                    "costStatus": "included", "pricingVersion": None,
                    "actualCostUsd": None, "estimatedCostUsd": 0.0,
                },
                "counters": {
                    "inputTokens": 100, "outputTokens": 20, "cacheReadTokens": 30,
                    "cacheWriteTokens": 0, "reasoningTokens": 5,
                    "apiCallCount": 2, "toolCallCount": 3,
                },
            }),
            encoding="utf-8",
        )
        csv_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.csv"
        csv_path.unlink()

        retried = ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="idempotent-finish",
            feature_name="Idempotent finish",
            finished_at=datetime.fromtimestamp(181, timezone.utc),
        )

        self.assertEqual(record, retried)
        self.assertTrue(csv_path.exists())
        self.assertFalse(snapshot_path.exists())
        history_lines = (self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(history_lines))

    def test_cli_start_and_finish_work_without_persisting_raw_session_data(self):
        script = SCRIPTS_DIRECTORY / "ai_usage.py"
        common = [
            sys.executable,
            str(script),
            "--root",
            str(self.root),
            "--state-db",
            str(self.state_database),
        ]

        started = subprocess.run(
            [*common, "start", "cli-smoke", "--session-id", "parent"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, started.returncode, started.stderr)
        self.assertNotIn("messages", started.stdout)
        self.assertTrue((self.root / ".ai-usage" / "cli-smoke.json").exists())

        finished = subprocess.run(
            [*common, "finish", "cli-smoke", "--feature-name", "CLI smoke"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, finished.returncode, finished.stderr)
        self.assertEqual("cli-smoke", json.loads(finished.stdout)["workId"])
        self.assertFalse((self.root / ".ai-usage" / "cli-smoke.json").exists())

    def test_cli_report_regenerates_csv_from_validated_history(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="report-smoke",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="report-smoke",
            feature_name="Report smoke",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )
        csv_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.csv"
        csv_path.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIRECTORY / "ai_usage.py"),
                "--root",
                str(self.root),
                "--state-db",
                str(self.state_database),
                "report",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual({"records": 1}, json.loads(completed.stdout))
        self.assertIn("report-smoke", csv_path.read_text(encoding="utf-8"))

    def test_report_preserves_legacy_measurement_boundary_and_notes(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="legacy-boundary",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="legacy-boundary",
            feature_name="Legacy boundary",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )
        history_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
        record = json.loads(history_path.read_text(encoding="utf-8"))
        record["measurementBoundary"] = "post-initial-investigation-through-final-local-validation"
        record["notes"] = "Initial repository inspection before the snapshot is excluded."
        history_path.write_text(json.dumps(record, separators=(",", ":")) + "\n", encoding="utf-8")

        ai_usage.regenerate_report(root=self.root)

        csv_text = history_path.with_suffix(".csv").read_text(encoding="utf-8")
        self.assertIn("post-initial-investigation-through-final-local-validation", csv_text)
        self.assertIn("Initial repository inspection before the snapshot is excluded.", csv_text)

    def test_report_accepts_legacy_record_without_notes(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="legacy-without-notes",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="legacy-without-notes",
            feature_name="Legacy without notes",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )
        history_path = self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl"
        record = json.loads(history_path.read_text(encoding="utf-8"))
        record.pop("notes")
        history_path.write_text(json.dumps(record, separators=(",", ":")) + "\n", encoding="utf-8")

        ai_usage.regenerate_report(root=self.root)

        self.assertIn("legacy-without-notes", history_path.with_suffix(".csv").read_text(encoding="utf-8"))

    def test_concurrent_finish_consumes_snapshot_exactly_once(self):
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="concurrent-finish",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        script = SCRIPTS_DIRECTORY / "ai_usage.py"
        command = [
            sys.executable,
            str(script),
            "--root",
            str(self.root),
            "--state-db",
            str(self.state_database),
            "finish",
            "concurrent-finish",
            "--feature-name",
            "Concurrent finish",
        ]

        processes = [
            subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for _ in range(2)
        ]
        results = [process.communicate(timeout=30) for process in processes]

        self.assertEqual([0, 0], [process.returncode for process in processes], results)
        records = [json.loads(stdout) for stdout, _ in results]
        self.assertEqual(records[0], records[1])
        history_lines = (self.root / "docs" / "engineering" / "ai-usage" / "feature-costs.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(history_lines))
        self.assertFalse((self.root / ".ai-usage" / "concurrent-finish.json").exists())

    def test_concurrent_start_rejects_overlapping_work_for_same_session(self):
        script = SCRIPTS_DIRECTORY / "ai_usage.py"
        common = [
            sys.executable,
            str(script),
            "--root",
            str(self.root),
            "--state-db",
            str(self.state_database),
            "start",
        ]
        processes = [
            subprocess.Popen(
                [*common, work_id, "--session-id", "parent"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for work_id in ("overlap-one", "overlap-two")
        ]
        results = [process.communicate(timeout=30) for process in processes]

        self.assertEqual([0, 2], sorted(process.returncode for process in processes), results)
        snapshots = list((self.root / ".ai-usage").glob("overlap-*.json"))
        self.assertEqual(1, len(snapshots))

    def test_finish_preserves_mixed_actual_and_estimated_costs(self):
        with closing(sqlite3.connect(self.state_database)) as connection:
            connection.execute(
                """
                UPDATE sessions
                SET actual_cost_usd = 1.0, estimated_cost_usd = NULL,
                    cost_source = 'provider', cost_status = 'actual'
                WHERE id = 'parent'
                """
            )
            connection.commit()
        ai_usage.start_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="mixed-costs",
            session_id="parent",
            captured_at=datetime.fromtimestamp(150, timezone.utc),
        )
        with closing(sqlite3.connect(self.state_database)) as connection:
            connection.execute(
                "UPDATE sessions SET actual_cost_usd = 1.5 WHERE id = 'parent'"
            )
            self.insert_session(
                connection,
                session_id="estimated-child",
                parent_session_id="parent",
                source="subagent",
                started_at=160,
                ended_at=170,
                estimated_cost_usd=0.25,
                cost_source="catalog",
                cost_status="estimated",
                pricing_version="2026-08-29",
            )
            connection.commit()

        record = ai_usage.finish_measurement(
            root=self.root,
            state_database=self.state_database,
            work_id="mixed-costs",
            feature_name="Mixed costs",
            finished_at=datetime.fromtimestamp(180, timezone.utc),
        )

        self.assertEqual("actual", record["mainAgent"]["cost"]["status"])
        self.assertAlmostEqual(0.5, record["mainAgent"]["cost"]["actualUsd"])
        self.assertEqual("estimated", record["delegatedAgents"][0]["cost"]["status"])
        self.assertEqual(
            {
                "status": "mixed",
                "actualUsd": 0.5,
                "estimatedUsd": 0.25,
                "pricingVersion": "2026-08-29",
            },
            record["cost"],
        )


if __name__ == "__main__":
    unittest.main()
