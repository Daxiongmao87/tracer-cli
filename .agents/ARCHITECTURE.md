# ARCHITECTURE.md — target Tracer architecture

## Product boundary

Tracer is an interactive terminal agent CLI. The production runtime must work on arbitrary user-selected working directories and open-ended tasks. It must not depend on benchmark fixtures, hard-coded task families, control/experimental arms, or eval oracles.

The current `harness.py` is a Phase-1 proof of concept that demonstrated the learned-affordance mechanism. It should be treated as eval/support code while its reusable pieces are extracted into the product runtime.

## Target runtime loop

The key architectural requirement is that retrieval happens **after the model has formed a next-step intent but before execution**:

```text
┌───────────────────────────────────────┐
│ interactive session                   │
│ user goal + conversation + workspace  │
└───────────────────┬───────────────────┘
                    ▼
              model deliberation
                    │
                    ▼
              next-step intent
                    │
                    ▼
        passive affordance retrieval
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
 relevant prior actions   no useful hit
         │                     │
         └──────────┬──────────┘
                    ▼
        model chooses/adapts action
                    │
                    ▼
           bash(intent, command)
                    │
                    ▼
               observation
                    │
                    ▼
        record outcome/experience
                    │
                    └───── repeat
```

The agent can always ignore retrieved affordances and use arbitrary Bash. Retrieval narrows attention; it does not close the action space.

## Logical components

A likely product decomposition is:

```text
tracer/
├── cli / tui            interactive conversation and session UX
├── sessions             create/list/select/persist/resume sessions
├── context              active-context assembly and compaction
├── agent_loop           model deliberation, action selection, observations
├── model_provider       replaceable completion/model interface
├── bash                 primitive shell execution boundary
├── environment          compact workspace/environment fingerprinting
├── memory               durable episodic affordance store
├── retrieval            semantic/contextual retrieval and reranking
├── affordances          optional derived prototypes/templates
└── safety               execution policy, gating, redaction, approvals

eval/
├── harness              controlled treatment/control comparisons
├── fixtures             test repositories
├── oracles              independent deterministic checks
└── results              reproducible experiment artifacts
```

The exact filenames can change. The separation of concerns should not.

## Session persistence and resume

A Tracer session is durable product state, not merely an in-memory message list. Exiting the CLI must not destroy an unfinished working session.

The runtime should persist enough information to support at least:

- a stable session identifier and timestamps,
- workspace/repository association,
- compacted semantic/task state,
- relevant recent conversation retained verbatim,
- current task/progress and unresolved work,
- user constraints and important decisions,
- discovered workspace facts needed for continuity,
- changed-file awareness or equivalent working-state information,
- model/provider/session metadata needed to reconstruct the interaction safely.

The CLI should be able to create a new session, list existing sessions, select one, and resume it after process restart. Resume should reconstruct the active model context from persisted compacted state plus the appropriate recent history; it should not require replaying an indefinitely growing raw transcript.

Session persistence is distinct from learned-affordance memory. Deleting or compacting a conversation must not implicitly rewrite the procedural experience store, and retrieving an affordance must not be treated as reconstruction of the current task state.

## Context compaction

Long-running sessions will eventually exceed the useful context budget of the selected model. Tracer must treat compaction as a normal runtime operation rather than solving this with blind message truncation.

A compaction cycle should conceptually:

```text
raw session history + current task state
        ↓
context-pressure threshold reached
        ↓
identify an older stable history region
        ↓
produce/update durable compacted session state
        ↓
retain recent turns and active tool interactions verbatim
        ↓
rebuild active model context
        ↓
continue the same session
```

Compaction must preserve information whose loss could change subsequent behavior, including:

- explicit user requirements and constraints,
- decisions already made and rejected alternatives where still relevant,
- discovered repository/workspace facts,
- important command/tool outcomes,
- files created/modified/deleted and the purpose of those changes,
- current plan/progress when one exists,
- unresolved failures, questions, or TODOs,
- safety/approval state that remains relevant.

Large or repetitive raw command output should not be retained indefinitely when a bounded semantic result is sufficient. Recent turns should remain verbatim so the interaction does not feel as if it resets after every compaction.

Compaction should be driven primarily by context pressure/token budget, not a fixed turn count. Its output should be durable so the same compacted state can be used for session resume after restart.

Compaction is **not** learned-affordance consolidation. A compacted session summary describes the state of one conversation/workstream; an affordance episode records reusable evidence that a particular action worked for a particular intent/environment. Keep those data paths independently inspectable and testable.

## Primitive action

The conceptual primitive is:

```text
bash(intent, command)
```

`intent` describes what the agent is trying to accomplish at this action boundary. `command` is the concrete shell action. The runtime records the resulting observation and enough environment context to make the episode reusable later.

A durable episode should contain, at minimum, information equivalent to:

```json
{
  "intent": "locate references to the failing symbol",
  "command": "rg -n 'WidgetFactory' src tests",
  "environment": "<workspace/context fingerprint>",
  "observation": "<bounded result summary>",
  "outcome": "<success/failure and quality signals>",
  "timestamp": "..."
}
```

The schema may evolve. The important rule is that observed experience is primary evidence.

## Retrieval

Retrieval should use the current intent plus relevant environment/session context. It may evolve from lexical retrieval to embeddings and reranking, but it must remain implementation-independent from the agent loop.

Candidate signals include:

- semantic similarity of intent,
- workspace/environment similarity,
- structural similarity of normalized shell actions,
- prior success/failure,
- retries or corrective actions that followed,
- execution latency and output usefulness,
- recency and repeated successful reuse.

Do not require a manually maintained semantic taxonomy to make retrieval work.

## Derived affordances

Raw episodes are sufficient for the first useful implementation. When repeated evidence supports it, Tracer may derive disposable higher-level affordances such as parameterized command templates or prototypes. These are derivative cache entries, not ground truth.

Example:

```text
rg -n TODO src/
rg -n FIXME lib/
rg -n WidgetFactory packages/
```

may support a derived pattern roughly equivalent to:

```text
rg -n {query} {path}
```

A generated name such as `prototype_87` is sufficient. Tracer does not need a permanent curated ontology such as `search.source.recursive`.

## Interactive CLI requirements

The CLI should support an ongoing user session rather than one-shot benchmark cells. At minimum the architecture should permit:

- arbitrary natural-language tasks,
- multi-step agent execution,
- visible action/observation flow appropriate for a terminal agent,
- interruption and follow-up by the user,
- durable session creation/listing/selection/resume,
- context-budget-aware compaction for long sessions,
- workspace-aware persistent affordance memory,
- configurable model/provider access,
- clear safety/approval handling for consequential commands.

The exact UX can iterate, but an eval dashboard is not a substitute for this interface.

## Current implementation gap

At present, `harness.py` combines agent loop, model calls, memory, retrieval, fixtures, task definitions, oracles, and experiment sweeping in one program. It bounds message history by dropping older messages; that is not product-grade context compaction. It also does not provide durable resumable interactive sessions. `tui.py` visualizes the experiment rather than an ongoing user session.

Product work should extract/generalize the agent, session, context-compaction, Bash, memory, retrieval, environment, provider, and safety concerns first. The existing eval should then call the product components as a consumer, so the benchmark measures the same runtime users actually run.
