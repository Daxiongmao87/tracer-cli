# CONVENTIONS.md — code and repo conventions

## Product vs eval

Tracer is an interactive terminal agent CLI. Keep a clear boundary between product/runtime code and controlled evaluation code.

- Product runtime must work on arbitrary real workspaces and open-ended tasks.
- Eval-only concerns include fixture repositories, planted mutations, control/treatment arms, deterministic task oracles, and benchmark result aggregation.
- The eval should consume product components rather than duplicating or redefining them whenever practical.
- Do not add product behavior solely to satisfy an eval oracle.

## Python and dependencies

- Preserve the existing Phase-1 harness sufficiently to reproduce published results.
- New product runtime code does **not** need to remain a single file or stdlib-only merely because the Phase-1 harness was. Choose dependencies deliberately and keep the runtime small, auditable, and portable.
- Keep concerns separated: provider, agent loop, Bash execution, environment context, memory, retrieval, derived affordances, safety, and terminal UI should have clear interfaces.
- Avoid framework lock-in where a small interface will do.

## Learned affordances

- Do not introduce a curated semantic command taxonomy as Tracer's core mechanism.
- Raw observed episodes are primary evidence. Normalized commands, embeddings, clusters, templates, prototypes, and macros are derived artifacts.
- Derived affordances should retain enough provenance to understand which experiences produced them.
- Cache misses must fall back cleanly to raw Bash.
- Retrieval must remain advisory; retrieved actions are never auto-authorized.

## Data

- Keep evaluation artifacts under `runs/` curated: published result summaries, primary run logs, and stores needed to reproduce claims. Scratch output stays uncommitted.
- Product/session memory should live in a separate runtime-appropriate store rather than being conflated with committed eval JSONL.
- Schema changes should be explicit and migration/version behavior documented. Do not silently reinterpret historical evaluation records.
- Never store credentials or secret-bearing environment data in learned memory.

## Fixtures

- Fixtures belong to evaluation only.
- Mutations happen through eval setup functions at run time.
- Never hand-edit a fixture merely to make an eval pass. Fix a broken baseline explicitly and re-run the affected evaluation.

## Commits

- One logical change per commit with an imperative subject line.
- Security-relevant changes (execution policy, approvals, credentials, networking, timeouts, cwd/workspace handling, memory sanitization) must say so in the commit and remain consistent with `SECURITY.md`.
- Claims about measured behavior must match the actual result artifacts.
- Product implementation changes should be verified through the real interactive CLI path in addition to automated tests/evals where applicable.

## Docs

- `.agents/` docs are normative for agent contributors.
- If implementation and documentation disagree, state which is current reality and fix the drift; do not silently pretend planned architecture already exists.
- Keep product vision, target architecture, and measured experimental results distinct.
- Mark speculation as speculation. Measured numbers belong in result artifacts; planned work belongs in `ROADMAP.md`.
