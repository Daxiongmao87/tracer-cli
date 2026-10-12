# Changelog

## Product identity correction — 2026-10-12

The repository documentation previously allowed the Phase-1 evaluation harness to become synonymous with **Tracer** itself. That was incorrect.

Tracer's product target is an **interactive terminal AI agent CLI** with learned-affordance memory. The Phase-1 harness, fixtures, result logs, and eval TUI are supporting proof-of-concept/evaluation artifacts used to validate that memory mechanism.

Accordingly, the historical `1.0.0` entry below describes what was shipped in that commit, but it must **not** be read as the final Tracer product contract or target UX. The current roadmap prioritizes extracting the reusable runtime and building the actual interactive CLI.

## [1.0.0] — 2026-10-11

This release marker captured the Phase-1 eval harness as a consistent reproducible artifact with an eval-oriented terminal frontend. In hindsight, calling that bundle the Tracer product contract was too broad; it is now treated as the Phase-1 prototype/evaluation baseline.

**Added**

- `tui.py` — a stdlib curses front end over the harness result contract.
  - **Watch mode** (`--file runs/run-<ts>.jsonl`): renders the live eval grid
    — one row per `(arm, run, repo, task)` cell, showing control then
    experimental `O`/`X` with step count — and a summary panel (per-arm
    totals, transfer ladder, success per task).
  - **Run mode** (no `--file`): spawns `harness.py`, polls its `--out` file,
    and renders progress live; on harness exit it shows the stderr tail
    instead of crashing.
  - **Print mode** (`--file ... --print`): the summary as plain text, for
    scripts and assertions.
  - Keys: `t` summary, `←`/`→` run, `r` re-run (run mode), `p` pause/resume,
    `q` quit.

**Fixed**

- `harness.py`: `retrieve()` now filters blocklisted commands too
  (SECURITY.md: "blocklist, twice"). Previously the blocklist was enforced at
  store time only; since it only grows, a stored action could match a pattern
  added later and still be suggested. Retrieval now re-checks.
- `harness.py`: removed dead `VENV_PY` constant (`PYTEST` uses `python3`).

**Corrected docs (at that time)**

- Control/arm descriptions in `README.md` and `.agents/ARCHITECTURE.md`: both
  arms require an intent each step; the arms differ only in store + retrieval.
- `.agents/SECURITY.md` and `README.md`: cwd is a fixture-scoped working
  directory, not a sandbox.
- `runs/RESULTS-phase1.md`: store count corrected to 94 experiences
  (33 distinct commands).

### Historical Phase-1 bundle

1. `harness.py`: agent loop, store, retrieval, oracles, metrics.
2. `tui.py`: live eval grid + summary over the harness results.
3. Fixtures and curated result artifacts used to reproduce the Phase-1 comparison.

For the current product contract and implementation direction, see `README.md` and `.agents/VISION.md`, `.agents/ARCHITECTURE.md`, and `.agents/ROADMAP.md`.
