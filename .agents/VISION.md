# VISION.md — what tracer is for

## The bet

Tool-using agents today start every session with the same fixed action
space: a registry of tools someone else designed. Humans don't work that
way — we accumulate *affordances* from experience: "last time the tests
were red in this repo, `git status` then `pytest -q` told me where to
look." Tracer is infrastructure for that: an agent that manufactures its
own useful action space online, from its own successful actions.

Phase 1 tested the smallest possible version of the bet: store successful
`(intent, command)` pairs, retrieve the top-5 most similar before each
step, present them as disposable affordances (use / modify / ignore). It
worked — modestly, measurably: higher success, fewer steps, no pollution on
unrelated tasks. The bet survives first contact with data.

## Where it goes

1. **Better memory** (phase 2): shell-AST normalization so `pytest -q`
   and `python -m pytest -q` are recognized as the same action; lazily
   synthesized templates so the cache stores *patterns*, not just
   episodes; quality weighting so fast, decisive actions outrank slow,
   flailing ones.
2. **Honest memory**: decay and forgetting. A cache that only grows
   becomes a junk drawer. Retrieval pollution is the failure mode to
   watch — phase 1's unrelated-project transfer test exists to catch it
   early, and it must survive every phase.
3. **Portable memory**: a tracer sidecar any agent loop can query —
   "given my intent and environment, what worked last time?" — without
   buying into a framework.

## What tracer is not

- **Not a tool registry.** Registries are designed top-down; affordances
  are learned bottom-up. Tracer never ships a curated skill list.
- **Not a prompt library.** Stored actions are evidence of what worked,
  not advice about what should work. The agent may ignore every
  retrieved affordance.
- **Not a planner.** Tracer doesn't decide what to do; it changes the
  texture of the action space the decider chooses from.
- **Not a replacement for verification.** Oracles stay deterministic and
  external. A fluent agent that can't be checked is a liability with a
  good memory.

## The standard

Every phase must be runnable, measured against a control, and honest
about cost. Phase 1 cost ~9% more tokens and didn't save wall time —
that's in the report, not buried. A phase that improves success while
hiding its price hasn't passed.
