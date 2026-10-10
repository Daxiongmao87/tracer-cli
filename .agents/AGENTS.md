# AGENTS.md — operating guide for AI agents in tracer-cli

## What this repo is

Tracer studies whether a terminal agent gets better at acting by remembering
what worked. Phase 1 is done and showed the basic effect (see
`runs/RESULTS-phase1.md`): an agent that stores successful actions and
retrieves the top-5 similar ones before each step succeeds more often with
fewer steps than a bash-only baseline. Everything here serves that
investigation. If a change doesn't serve the investigation, it doesn't belong.

## Before you touch experiment design

Read, in this order:

1. [VISION.md](VISION.md) — what tracer is for and what it is not
2. [ARCHITECTURE.md](ARCHITECTURE.md) — how the harness actually works
3. [EVAL.md](EVAL.md) — the eval protocol; what counts as signal
4. [SECURITY.md](SECURITY.md) — non-negotiable safety rules
5. [ROADMAP.md](ROADMAP.md) — what's planned vs what's merely an idea

## Running the experiment

```bash
bash fixtures/setup.sh          # one-time: git-init the fixtures
python3 harness.py --arms both --runs 2 --model <model>
```

`harness.py` calls the model via `atelier_chat()` (currently wired to
`atelier.astralkeep.com`). To run elsewhere, replace that one function with
your endpoint — the agent loop, store, and oracles don't care where
completions come from. Keep `max_tokens >= 1024` for reasoning models; short
budgets return empty content and silently poison results.

## Repo discipline

- **Fixtures stay pristine.** The harness mutates them and resets via git.
  Never hand-edit fixture sources to "fix" a task; the planted bugs and
  mutations are the test. If a fixture's baseline is wrong, say so and fix
  the baseline in a separate commit, then re-run.
- **`runs/` is curated, not a log dump.** Commit `RESULTS-*.md` summaries,
  the primary run log, and the learned store for a completed phase. Scratch
  runs, 0-byte stores, and superseded logs stay local.
- **Store schema is append-only.** Never rewrite history in a committed
  `store-*.jsonl`; if the schema changes, bump the phase and start a new
  store.
- **No new dependencies without a reason.** The harness is stdlib-only
  Python plus `rg`, `pytest`, `node`. Keep it that way unless the experiment
  demands otherwise.
- **The blocklist only grows.** See SECURITY.md. Weakening it is a
  security-relevant change: document why, in the commit.

## Making changes

- Answer the narrow question asked; don't rebuild the harness around it.
- Phase-1's minimalism is load-bearing: no taxonomy, no clustering, no
  templates, no AST normalization in the phase-1 code path. Phase-2 ideas
  go behind a flag or in a new module, never by complicating the baseline.
- Control and experimental arms must stay identical except for the
  treatment. If you touch the agent loop, check both arms still differ only
  in the intended way.
- Verify against the artifact: after a run, read the actual `runs/*.jsonl`
  before claiming results. Never summarize a run you haven't opened.
