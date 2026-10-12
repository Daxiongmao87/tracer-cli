# ROADMAP.md — where Tracer goes next

## Immediate priority: turn the proof of concept into the product

Phase 1 established that even crude episodic retrieval can help. The next priority is **not another benchmark frontend**. It is to build the actual interactive Tracer CLI and make the existing eval harness exercise that same runtime.

### 1. Extract the reusable runtime

Separate the current monolithic `harness.py` into product components for:

- model/provider access,
- interactive agent loop,
- `bash(intent, command)` execution,
- environment/workspace fingerprinting,
- episodic memory storage,
- retrieval/reranking,
- safety/policy boundaries.

Fixture setup, hard-coded eval tasks, control/experimental arms, and deterministic oracles remain eval-only concerns.

### 2. Build the interactive CLI/TUI

Tracer should run in a real working directory and accept arbitrary conversational tasks, broadly like an interactive terminal coding agent. The user should be able to start a session, issue a task, observe actions/results, interrupt or follow up, and continue working in the same context.

The current curses UI is an eval dashboard. It may provide reusable terminal rendering code, but it is not the target user experience.

### 3. Put retrieval at the correct action boundary

Move from “retrieve before asking the model what to do” toward the intended loop:

```text
observe → deliberate → next intent → retrieve → choose/adapt/fallback → bash → observe
```

The model should form a semantic next-step intent first; Tracer then retrieves relevant prior affordances before concrete execution is selected.

### 4. Make memory persistent and workspace-aware

Use a durable local store suitable for normal interactive use. Preserve raw episodes as primary evidence. Retrieval should account for semantic intent and workspace/environment context without hard-coding a domain taxonomy.

### 5. Upgrade retrieval incrementally

Once the interactive baseline works, evaluate improvements independently:

1. embedding-based intent/context retrieval,
2. shell-AST or structural command normalization,
3. quality-weighted reranking,
4. lazy template/prototype synthesis from repeated episodes,
5. decay/forgetting and pollution control,
6. repeated-sequence or macro discovery where evidence warrants it.

Each feature should earn its complexity through measured improvement.

## Supporting evaluation track

Keep the Phase-1 control/eval machinery reproducible and adapt it to consume the extracted product runtime. Continue measuring:

- task success,
- Bash/action count,
- failed actions,
- token use,
- wall time,
- same-project reuse,
- similar-project transfer,
- unrelated-project retrieval pollution.

The eval tells us whether memory changes help. It does not determine the product architecture.

## Later directions

- **Cross-session memory:** useful affordances survive CLI restarts.
- **Cross-agent memory:** test whether one model/agent can benefit from another's episodes without excessive pollution.
- **Portable memory service:** expose Tracer's memory/retrieval subsystem as a sidecar or API for other agent loops after the Tracer CLI itself is healthy.
- **Learned higher-order actions:** derive reusable multi-step behaviors from repeated successful traces without introducing a curated skill taxonomy.

## Standing non-goals

- No curated command/tool taxonomy as the core learning mechanism.
- No static prompt-library masquerading as memory.
- No product UX centered on benchmark matrices or control arms.
- No removal of raw Bash as the open-world fallback.
- No weakening of safety boundaries to improve benchmark numbers.
