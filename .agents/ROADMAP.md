# ROADMAP.md — where tracer goes next

## Phase 2 (planned — only because phase 1 showed the basic effect)

Three experiments, run in order, each against the phase-1 baseline:

1. **Shell-AST normalization.** Parse commands into normalized ASTs so
   `pytest -q` and `python -m pytest -q` retrieve as the same action.
   Question: does canonicalization beat raw episodic retrieval?
2. **Lazy templates.** Synthesize parameterized templates from clusters
   of similar episodes (derivative cache entries, clearly marked, never
   presented as ground truth). Question: do templates transfer better
   than raw episodes to similar projects?
3. **Quality-weighted ranking.** Weight by execution time, corrective
   steps that followed, and retry counts — fast, decisive actions
   outrank slow, flailing ones. Question: does quality signal beat
   recency/frequency?

Each experiment keeps the unrelated-project pollution check. If
normalization or templates cause nodeblog to degrade, that's a finding,
not a failure — report it.

## Phase 3 (ideas, not commitments)

- **Decay and forgetting.** A cache that only grows becomes a junk
  drawer. Time- and usefulness-based eviction, measured against the
  pollution check.
- **Embedding retrieval.** Phase 1 used TF-IDF because no embeddings
  endpoint was available. Re-run the comparison when one is.
- **Cross-agent stores.** Can one agent's learned affordances help
  another's? Shared vs private stores, with the pollution check as
  referee.
- **Tracer sidecar.** A small service any agent loop can query:
  "given intent + environment, what worked last time?" — no framework
  buy-in required.

## Non-goals (standing)

- No curated tool/skill registry. Learned bottom-up or not at all.
- No prompt-library features. Stored actions are evidence, not advice.
- No weakening of the security model to chase numbers.
