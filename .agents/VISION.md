# VISION.md — what Tracer is for

## Product

Tracer is an **interactive terminal AI agent CLI**: a user launches it in a working directory, gives it open-ended tasks, and collaborates with an agent that reasons, acts through the shell, observes results, and continues interactively. Its broad product category is similar to OpenCode; its distinguishing idea is that its useful action space is learned from experience instead of being fixed entirely by a tool registry designed in advance.

Tracer begins from a deliberately small primitive capability centered on:

```text
bash(intent, command)
```

The explicit intent is not decorative metadata. It is the semantic handle used to associate what the agent is trying to accomplish with what actually worked.

## The bet

Tool-using agents normally begin every session with a fixed action space authored by somebody else. Tracer tests and productizes a different approach: retain successful intent/action/environment/outcome episodes and use them to make relevant prior behavior available at the moment the agent is deciding what to do next.

The target interaction loop is:

```text
user goal / latest observation
        ↓
deliberate: what should I accomplish next?
        ↓
express next intent
        ↓
passive retrieval of relevant learned affordances
        ↓
choose one / adapt one / ignore all and use raw Bash
        ↓
execute
        ↓
observe
        ↓
record experience
        ↓
repeat
```

This is an online learned affordance cache: experience changes the texture of the future action space without closing the world around a static registry.

## Durable interactive work

Tracer is meant for work that can outlive a single context window or a single CLI process. Session continuity is therefore part of the product, not incidental UX.

A session should be persistable, discoverable, and resumable after exit. Resuming should restore enough state for the agent and user to continue naturally: workspace association, task progress, user constraints, important decisions, relevant recent history, discovered facts, changed-file state, and unresolved work.

Long sessions must also survive context pressure. Instead of simply dropping old messages, Tracer should compact older conversational and tool history into a durable semantic/session representation while retaining recent turns verbatim. The purpose of compaction is continuity, not merely token reduction.

Three forms of retained state must remain conceptually distinct:

- **conversation/session context** — compacted to let one long-running interaction continue;
- **workspace/task state** — what is currently true, what changed, and what remains to do;
- **learned affordance memory** — reusable evidence connecting intent, environment, action, and outcome across work.

Compaction must not silently turn conversation summaries into procedural affordances, and affordance retrieval must not substitute for reconstructing the state of a resumed session.

## Why this matters

- **Open-world capability.** A cache miss never prevents action because Bash remains available.
- **Procedural memory.** Discoveries about a repository, toolchain, or workflow do not have to be rediscovered every session.
- **Continuity.** Users can leave and resume real work without restarting the conversation from scratch.
- **Long-horizon operation.** Compaction lets sessions continue beyond a single raw model context without blind truncation.
- **Small active action space.** The model sees a few contextually relevant affordances rather than a huge global catalog.
- **Emergent specialization.** The same Tracer binary can develop different useful habits in different projects and environments.
- **Potential efficiency gains.** Familiar operations can become recognition/reuse problems instead of repeated reasoning/exploration problems.

## Learned, not curated

Tracer must not solve this by embedding an unmaintainable command taxonomy or hand-authored skill hierarchy. Durable ground truth is the history of observed episodes. More abstract representations may be derived from that history:

- shell/command structural normalization,
- semantic embeddings of intent and context,
- clusters of similar episodes,
- lazily synthesized parameterized templates,
- higher-order prototypes or repeated action sequences,
- quality signals derived from success, retries, corrective actions, latency, and downstream progress.

Those abstractions are caches over experience, not a replacement for it. They should be revisable as evidence improves.

## What Tracer is not

- **Not an eval harness.** The existing Phase-1 benchmark validated the core memory idea; it is supporting test infrastructure, not the product.
- **Not a static tool registry.** Tracer may expose a small set of true primitives, but learned affordances are bottom-up rather than curated top-down.
- **Not a prompt library.** Stored actions are evidence of prior behavior and outcomes.
- **Not a closed action system.** Raw Bash remains the escape hatch for novel work.
- **Not memory without an agent.** The memory layer is Tracer's differentiator, but the product is the complete interactive agent CLI around it.
- **Not ephemeral chat.** A useful Tracer session must be resumable and able to survive context-window pressure through compaction.

## Evaluation

Evaluation remains important because the learned-memory mechanism can easily become self-reinforcing noise. Controlled tests should measure task success, steps, failed actions, tokens, wall time, transfer, and retrieval pollution. Those tests answer whether a change improves Tracer; they do not define what Tracer is.

Interactive-runtime evaluation should additionally cover session continuity: verify that a session can be persisted, resumed after process restart, compacted under context pressure, and continued without losing material user constraints, workspace facts, decisions, changed-file awareness, or unresolved work.

Phase 1 established a useful first signal using raw episodic retrieval. Future evaluations should continue to compare memory strategies honestly while product development moves toward the interactive CLI.
