# AI usage accounting

This directory contains privacy-preserving development-usage records.

## Sources of truth

- `feature-costs.jsonl` is the append-only canonical history, with one validated object per work unit.
- `feature-costs.csv` is a derived human-readable view. Regenerate it with `python scripts/ai_usage.py report`; do not edit it manually.
- `.ai-usage/` contains local starting snapshots and persistent lock files. It is ignored by Git.

No prompt, response, reasoning text, credential, source-file content, header, cookie, or arbitrary session metadata may be stored. Session IDs and allowlisted technical accounting fields are retained solely for reconciliation.

## Measurement boundary

The standard boundary is `development-through-final-local-validation`:

1. start immediately before investigation or implementation;
2. finish after all local tests and independent review have completed;
3. commit, push, CI waiting, telemetry persistence itself, and final status messages remain outside the measurement.

A missing starting snapshot cannot be reconstructed. Mark such work unavailable rather than estimating it from time, diff size, messages, or commits.

## Commands

Run from the repository root with Python 3.11 or later.

```bash
python scripts/ai_usage.py start <work-id> --session-id <hermes-session-id>

python scripts/ai_usage.py finish <work-id> \
  --feature-name "Short feature name" \
  --pr-number 3 \
  --pr-url https://github.com/edupinhata/NotepadPoweredBacklog/pull/3 \
  --commit-sha 0123456789abcdef0123456789abcdef01234567

python scripts/ai_usage.py report
```

`--state-db` is normally unnecessary: the collector derives `state.db` from `hermes config path`. Use an explicit path only when operating against a verified non-default profile.

The operator or agent must supply the exact current Hermes session ID. The collector deliberately refuses to guess the latest session because that could attribute unrelated work.

## Fail-closed behavior

The collector:

- validates the exact snapshot and history schemas before accounting;
- rejects missing, negative, boolean, non-finite, backward, or contradictory counters and costs;
- rejects provider/model drift and overlapping or active delegated sessions;
- follows the full linked subagent tree and counts each session once;
- separates input, output, cache reads, cache writes, and reasoning;
- defines `totalTokens` as input plus output only;
- preserves actual, estimated, included, partial, mixed, and unavailable cost semantics;
- serializes concurrent finalization with persistent interprocess locks;
- writes JSONL and CSV using flushed, same-directory atomic replacement;
- consumes a starting snapshot only after canonical history is committed;
- supports an idempotent retry that repairs the CSV without appending a duplicate record.

If finalization fails before the JSONL commit, the starting snapshot remains available for diagnosis and retry. If JSONL succeeds but CSV generation or cleanup fails, an identical retry repairs the derived view and removes the leftover snapshot without adding another record.

## Verification

```bash
python -m unittest discover -s scripts/tests -v
python scripts/ai_usage.py report
```

The test suite includes a real two-process exactly-once finalization test on Windows-compatible file locks.
