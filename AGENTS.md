# AGENTS.md

This repo is **Tracer** — an experiment in learned affordances for terminal
agents. The full operating guide for AI agents working here lives in
[`.agents/AGENTS.md`](.agents/AGENTS.md). Start there.

Quick orientation:

- `harness.py` is the phase-1 experiment driver (two arms: bash-only
  control vs bash + learned affordance cache).
- `fixtures/` holds three small repos the harness mutates and resets.
  Run `bash fixtures/setup.sh` once before running the harness.
- `runs/` holds curated result artifacts, not scratch logs.
- `.agents/` holds vision, architecture, eval protocol, conventions,
  roadmap, and security docs. Read them before changing experiment design.
