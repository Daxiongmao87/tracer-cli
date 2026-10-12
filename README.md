# Tracer

Tracer is an **interactive terminal AI agent CLI** with learned procedural memory.

Like other terminal coding/agent tools, Tracer is intended to run inside a real working directory, accept open-ended conversational tasks, reason through them, execute shell actions, observe the results, and continue interactively. Its distinguishing idea is that it does not rely only on a fixed tool catalog: Tracer learns useful **affordances** from its own successful actions and retrieves them when similar intentions arise later.

The conceptual primitive is deliberately small:

```text
bash(intent, command)
```

Bash remains the universal fallback. Learned affordances make familiar work easier to rediscover; they do not prevent novel shell actions.

## Core idea

Tracer records episodes containing the agent's intent, the concrete action it took, relevant environment/workspace context, and the resulting outcome. At the next action boundary, the intended flow is:

```text
observe
  ↓
deliberate about the next goal
  ↓
express next-step intent
  ↓
retrieve relevant prior successful actions
  ↓
use / adapt / ignore them
  ↓
execute Bash
  ↓
observe + remember
```

Over time, repeated experience can support better retrieval, structural command normalization, lazily derived templates/prototypes, quality weighting, and eventually reusable higher-order actions. These abstractions should emerge from evidence rather than from a hand-maintained command taxonomy.

## Current status

The repository currently contains a **Phase-1 proof-of-concept/evaluation harness**, not yet the complete intended interactive product.

Phase 1 tested the smallest useful version of the memory idea: successful `(intent, command)` episodes were stored and the top five similar past actions were retrieved before subsequent steps. In the controlled run, the memory arm completed 22/24 tasks versus 20/24 for control and used fewer average Bash steps (3.8 vs 4.6), at roughly 9% more tokens and without a wall-time win. See [`runs/RESULTS-phase1.md`](runs/RESULTS-phase1.md).

Those results justify continuing the mechanism. They do **not** define Tracer as an eval harness.

The present files reflect that prototype history:

- `harness.py` — Phase-1 controlled experiment driver; currently mixes agent loop, memory, retrieval, fixture tasks, and oracles.
- `tui.py` — current eval-results TUI; useful scaffolding, but not the target interactive agent interface.
- `fixtures/` — small repositories used for controlled evaluation.
- `runs/` — Phase-1 result artifacts and learned stores.
- `.agents/` — product vision, target architecture, implementation roadmap, eval protocol, conventions, and security guidance.

## Product direction

The next engineering priority is to extract the reusable runtime from the experiment and build the actual interactive Tracer CLI:

1. separate model/provider, agent loop, Bash execution, environment context, memory, retrieval, and safety components;
2. build an ongoing conversational terminal session over arbitrary working directories;
3. place passive retrieval between next-step intent formation and concrete action execution;
4. persist workspace-aware episodic memory across normal sessions;
5. make the existing controlled eval harness consume the same product runtime rather than defining it;
6. then improve retrieval with embeddings, structural normalization, quality weighting, lazy templates/prototypes, and forgetting/decay, measuring each change against the baseline.

See [`.agents/VISION.md`](.agents/VISION.md), [`.agents/ARCHITECTURE.md`](.agents/ARCHITECTURE.md), and [`.agents/ROADMAP.md`](.agents/ROADMAP.md).

## Design principles

- **Interactive agent first.** Benchmarking exists to validate the product, not to become the product.
- **Bash stays open-world.** A missing learned affordance must never make an action impossible.
- **Intent is semantic state.** It provides the retrieval key for what the agent is trying to accomplish next.
- **Experience is ground truth.** Raw observed episodes remain primary; abstractions are derivative caches.
- **No curated command ontology.** Useful action structure should be induced from experience wherever practical.
- **Retrieval is advisory.** A retrieved command is not permission to execute it and can always be ignored.
- **Measure memory honestly.** Success, action count, failures, token cost, latency, transfer, and retrieval pollution all matter.

## Running the existing Phase-1 eval

The current repository can still reproduce the proof-of-concept experiment:

```bash
bash fixtures/setup.sh
python3 harness.py --arms both --runs 2 --model <your-model>
```

`harness.py` currently calls the model through `atelier.astralkeep.com`; provider access is expected to become replaceable as the product runtime is extracted.

The eval is retained because it provides a controlled regression test for the learned-affordance mechanism while Tracer evolves into the interactive CLI described above.
