# AGENTS.md — operating guide for AI agents in tracer-cli

## What this repo is

Tracer is an **interactive terminal AI agent CLI**. Its product category is similar to OpenCode and other terminal coding/agent tools: a user opens Tracer in a real working directory, gives it an open-ended task, and interacts with an agent that reasons, acts through the shell, observes results, and continues until the task is complete.

Tracer's differentiator is **learned affordances**. The runtime starts from a deliberately small primitive action space centered on `bash(intent, command)`. Successful actions are remembered with their intent, environment, command, and outcome. Between deliberation and execution, the harness passively retrieves relevant prior actions and presents them as temporary affordances. The model may use, adapt, or ignore them; raw Bash always remains available.

The repo currently contains a Phase-1 evaluation harness that validated a minimal version of this idea. That harness is supporting evidence and test infrastructure. **It is not Tracer's product definition, target UX, or target architecture.** Do not turn Tracer into an eval runner.

## Product invariants

1. **Interactive agent CLI first.** The primary user experience is an ongoing terminal conversation/session over arbitrary real work, not a benchmark matrix.
2. **Sessions are persistent and resumable.** A user must be able to exit Tracer, later list/select a prior session, and resume it with its workspace association, task progress, compacted state, and relevant recent history restored.
3. **Long sessions compact instead of truncating blindly.** Context pressure must trigger deliberate compaction of older conversation/tool history into durable session state while recent turns remain available verbatim. Compaction must preserve user constraints, decisions, discovered workspace facts, important tool outcomes, changed files, unresolved work, and other state required for continuity.
4. **Session state and affordance memory are separate systems.** Compaction preserves one conversation/task across context limits; affordance memory stores reusable intent/action/environment/outcome experience across work. Do not collapse them into one store or treat a compacted transcript as learned procedural memory.
5. **Bash is the universal fallback.** Tracer must remain able to perform novel actions even when nothing useful is retrieved from memory.
6. **Intent precedes retrieval.** The desired loop is: observe → deliberate/express next intent → retrieve relevant affordances → choose/adapt/fallback → execute → observe → remember.
7. **Memory is passive assistance, not authority.** Retrieval is never permission to execute and never removes the model's ability to choose another action.
8. **No curated taxonomy.** Do not introduce a hand-maintained `git.*`, `python.*`, `filesystem.*`, or similar ontology as the core design. Reusable actions should emerge from episodes, structural normalization, clustering/generalization, and measured reuse.
9. **Ground truth is experience.** Durable records are observed intent/action/environment/outcome episodes. Templates, prototypes, clusters, and higher-order affordances are derivative cache artifacts and may be regenerated or revised.
10. **Evaluation supports the product.** Control arms, fixtures, deterministic oracles, and transfer tests exist to measure whether changes improve Tracer. Product architecture must not be distorted to make the benchmark convenient.

## Read before changing architecture

Read, in this order:

1. [VISION.md](VISION.md) — product purpose and principles
2. [ARCHITECTURE.md](ARCHITECTURE.md) — target runtime architecture and current gap
3. [ROADMAP.md](ROADMAP.md) — product-first implementation order
4. [SECURITY.md](SECURITY.md) — non-negotiable shell safety boundaries
5. [EVAL.md](EVAL.md) — supporting evaluation protocol

## Current repository state

The current implementation is a proof of concept:

- `harness.py` runs controlled tasks across fixture repositories and compares memory vs no-memory arms.
- `tui.py` currently visualizes that eval harness.
- `fixtures/` and `runs/` are eval assets.
- Phase 1 showed a modest measurable benefit from episodic retrieval.
- The current harness's bounded message window is not acceptable product compaction and does not satisfy the persistent-session requirement.

Do not mistake those current files for the desired end state. The next engineering work should extract/generalize the useful agent loop and memory mechanisms into the interactive CLI rather than adding more product surface to the benchmark runner.

## Working rules

- Preserve Phase-1 results and reproducibility; move or isolate eval code rather than destroying evidence.
- Product runtime code must not depend on fixture repositories, hard-coded task families, control/experimental arms, or deterministic eval oracles.
- Treat session persistence, resume, and context compaction as baseline runtime capabilities, not optional polish for a later release.
- A resumed session should continue from persisted semantic/task state; do not require replaying an unbounded raw transcript to reconstruct continuity.
- Compaction must be testable: verify that important constraints, decisions, workspace facts, file-change state, and unresolved tasks survive compaction and resume.
- Keep model/provider access replaceable. Atelier is one endpoint, not Tracer's conceptual boundary.
- Keep retrieval and memory interfaces separable from the model loop so alternative embedding/retrieval strategies can be tested without rewriting the CLI.
- Make changes incrementally and verify the user-facing CLI path as well as automated tests/evals.
- Do not claim the current implementation already satisfies this architecture when it does not.
