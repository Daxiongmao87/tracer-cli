# Changelog

Versioning follows the marker in [`VERSION`](VERSION). Tracer treats
`1.0.0` as: the phase-1 eval harness, shipped as a consistent whole with a
user-facing terminal frontend — no internal/external drift in what it claims
to do.

## [1.0.0] — 2026-10-11

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

**Corrected docs (no code change)**

- Control/arm descriptions in `README.md` and `.agents/ARCHITECTURE.md`: both
  arms require an intent each step; the arms differ only in store + retrieval.
- `.agents/SECURITY.md` and `README.md`: cwd is a fixture-scoped working
  directory, not a sandbox — the blocklist + human supervision bound the
  blast radius.
- `runs/RESULTS-phase1.md`: store count corrected to 94 experiences
  (33 distinct commands).

### Contract (what 1.0.0 comprises)

1. The phase-1 harness (`harness.py`): agent loop, store, retrieval, oracles,
   metrics — run via `bash fixtures/setup.sh && python3 harness.py ...`.
2. The TUI (`tui.py`): live eval grid + summary, driving the harness or
   watching its results.
3. Consistency: every claim the docs make about the harness's behaviour is
   matched by the code, and every metric the UI displays reproduces the run
   log.
