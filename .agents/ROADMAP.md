# ROADMAP.md — where Tracer goes next

## Immediate priority: turn the proof of concept into the product

Phase 1 established that even crude episodic retrieval can help. The next priority is **not another benchmark frontend**. It is to build the actual interactive Tracer CLI and make the existing eval harness exercise that same runtime.

### 1. Extract the reusable runtime

Separate the current monolithic `harness.py` into product components for:

- model/provider access,
- interactive agent loop,
- durable session persistence/resume,
- context assembly and compaction,
- `bash(intent, command)` execution,
- environment/workspace fingerprinting,
- episodic affordance memory storage,
- retrieval/reranking,
- safety/policy boundaries.

Fixture setup, hard-coded eval tasks, control/experimental arms, and deterministic oracles remain eval-only concerns.

### 2. Build the interactive CLI/TUI

Tracer should run in a real working directory and accept arbitrary conversational tasks, broadly like an interactive terminal coding agent. The user should be able to start a session, issue a task, observe actions/results, interrupt or follow up, and continue working in the same context.

The current curses UI is an eval dashboard. It may provide reusable terminal rendering code, but it is not the target user experience.

### 3. Make sessions durable and resumable

Implement session persistence as a baseline capability, not later polish. The user should be able to:

- create a new session,
- list prior sessions,
- select a previous session,
- exit Tracer without losing unfinished work,
- resume after process restart with workspace association, task progress, compacted state, user constraints, important decisions, relevant recent history, and unresolved work restored.

Resume should reconstruct active model context from persisted semantic/session state plus bounded recent history. It should not require replaying an unbounded transcript.

### 4. Add context-budget-aware compaction

Long-running sessions must survive model context limits without blind truncation. Add a compaction mechanism that activates under context pressure and:

- compacts an older stable portion of conversation/tool history,
- preserves user constraints, decisions, discovered workspace facts, important tool outcomes, changed-file state, progress, and unresolved work,
- keeps recent interaction verbatim,
- avoids retaining huge raw command outputs when bounded semantic results are sufficient,
- persists the compacted state so it also supports session resume.

Compaction quality needs explicit tests: force compaction mid-task, restart the CLI, resume, and verify that the agent still respects prior constraints and accurately understands what changed and what remains to do.

Do not conflate this with affordance-memory consolidation. Session compaction preserves one ongoing interaction; learned affordance memory stores reusable procedural experience across interactions.

### 5. Put retrieval at the correct action boundary

Move from “retrieve before asking the model what to do” toward the intended loop:

```text
observe → deliberate → next intent → retrieve → choose/adapt/fallback → bash → observe
```

The model should form a semantic next-step intent first; Tracer then retrieves relevant prior affordances before concrete execution is selected.

### 6. Make affordance memory persistent and workspace-aware

Use a durable local store suitable for normal interactive use. Preserve raw episodes as primary evidence. Retrieval should account for semantic intent and workspace/environment context without hard-coding a domain taxonomy.

This store is distinct from persisted session/context state. Session deletion, compaction, or resume mechanics must not accidentally rewrite learned procedural history.

### 7. Upgrade retrieval incrementally

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

Add product-runtime tests for:

- session persistence across CLI restart,
- listing/selecting/resuming prior sessions,
- forced context compaction during unfinished work,
- preservation of user constraints and decisions across compaction,
- preservation of workspace facts and changed-file awareness,
- preservation of unresolved work across compact → exit → resume,
- bounded active context growth over long sessions.

The eval tells us whether memory changes help. It does not determine the product architecture.

## Later directions

- **Cross-session affordance memory:** useful learned actions survive CLI restarts and can assist later sessions without replacing session-specific state.
- **Cross-agent memory:** test whether one model/agent can benefit from another's episodes without excessive pollution.
- **Portable memory service:** expose Tracer's memory/retrieval subsystem as a sidecar or API for other agent loops after the Tracer CLI itself is healthy.
- **Learned higher-order actions:** derive reusable multi-step behaviors from repeated successful traces without introducing a curated skill taxonomy.

## Standing non-goals

- No curated command/tool taxonomy as the core learning mechanism.
- No static prompt-library masquerading as memory.
- No ephemeral-only session model that loses work on exit.
- No blind fixed-turn truncation as a substitute for compaction.
- No product UX centered on benchmark matrices or control arms.
- No removal of raw Bash as the open-world fallback.
- No weakening of safety boundaries to improve benchmark numbers.
