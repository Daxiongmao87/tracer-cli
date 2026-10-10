# Tracer

Tracer is an experiment in **learned affordances** for terminal agents: an
agent that starts with only `bash(intent, command)` and gradually manufactures
its own useful action space from experience — an online learned affordance
cache, not a tool registry.

## Status: phase 1 complete (2026-10-10)

The phase-1 harness (`harness.py`) pits two arms against each other on
identical tasks:

- **Control:** bash only. No intent requirement, no memory.
- **Experimental:** bash + a short intent required each step + every
  successful action stored as
  `{intent, command, cwd_context, environment, result_summary, success}`
  + top-5 similar past successes retrieved before each invocation and
  presented as temporary affordances (use / modify / ignore).

Deliberately minimal: no taxonomy, clustering, templates, AST normalization,
or quality scoring. Retrieval is TF-IDF cosine over intent+environment text
(0.7 intent / 0.3 environment).

**Result (48/48 cells):** experimental 22/24 tasks vs control 20/24, 3.8 vs
4.6 average bash steps, 0.7 vs higher failed-step rate — at ~9% more tokens
and no wall-time win. Transfer improves on same/similar projects; no
retrieval pollution on the unrelated project. Full report:
[`runs/RESULTS-phase1.md`](runs/RESULTS-phase1.md).

## Design details

- **Fixtures:** three small repos — `pycalc` (Python/pytest, same-project
  transfer), `pytask` (Python/pytest, similar-project transfer), `nodeblog`
  (Node, unrelated-project transfer / pollution check).
- **Task families** (repeated per repo): `inspect` (report local changes),
  `search` (find all references to a symbol), `test` (run the suite, report
  pass/fail), `fix` (a bug is planted; find it, fix it, suite must pass).
- **Oracles are deterministic:** fixture reset via `git checkout -- . &&
  git clean -fdq` before each run; success is checked by re-running
  git/rg/the suite directly, never by trusting the agent's word.
- **Metrics per run:** task success, bash calls, failed bash calls,
  prompt/completion tokens, wall-clock seconds, done-flag, error.
- **Security gating:** a blocklist (destructive ops, credential-shaped
  literals) is applied at store time and retrieval time. Retrieval is never
  permission to execute — and all commands run in the sandboxed fixture
  repos anyway.

## Running it

```bash
# one-time: make fixtures git repos so the harness can reset them
bash fixtures/setup.sh

python3 harness.py --arms both --runs 2 --model <your-model>
```

`harness.py` currently calls the model through `atelier.astralkeep.com`
(see `atelier_chat`); point it at your own endpoint to run elsewhere.
Results land in `runs/run-<ts>.jsonl`; experience stores in
`runs/store-<arm>-<ts>.jsonl`.

## What's next

Phase 2 candidates (only because phase 1 showed the basic effect):

1. raw episodic retrieval vs + shell AST normalization
2. + lazily synthesized templates (derivative cache entries, not ground truth)
3. quality-weighted ranking (exec time, corrective steps after, retries)

See [`.agents/ROADMAP.md`](.agents/ROADMAP.md) and
[`.agents/VISION.md`](.agents/VISION.md) for the longer arc.

## Layout

- `harness.py` — agent loop, store, retrieval, oracles, metrics
- `fixtures/` — the three fixture repos + `setup.sh` to git-init them
- `runs/` — curated artifacts: `RESULTS-phase1.md`, the primary run log,
  the learned experimental store, and the nodeblog re-run log
- `.agents/` — operating docs for AI agents working in this repo
  (vision, architecture, eval protocol, conventions, roadmap, security)
