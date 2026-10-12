# AGENTS.md

This repo is **Tracer** — an interactive terminal AI agent CLI, in the same broad product category as tools such as OpenCode. Tracer's defining feature is a learned-affordance memory layer: the agent begins with Bash as its universal primitive, records successful intent/action/outcome episodes, and passively retrieves relevant prior actions between deliberation and execution so its useful action vocabulary improves through experience.

The current `harness.py`, fixtures, result logs, and eval TUI are **experimental scaffolding used to validate that mechanism**. They are not the product definition and must not be treated as the target architecture.

Read [`.agents/AGENTS.md`](.agents/AGENTS.md) before making changes.

Quick orientation:

- The product target is an **interactive agent CLI** that accepts open-ended user tasks and works in real repositories/directories.
- The runtime primitive is Bash, expressed with an explicit intent: `bash(intent, command)`.
- Between deliberation and execution, Tracer retrieves relevant learned affordances from prior successful actions and offers them as disposable suggestions; the agent may use, adapt, or ignore them and always retains raw Bash as a fallback.
- Learned affordances emerge bottom-up from experience. Do not replace this with a curated taxonomy, static skill registry, or hand-maintained command catalog.
- `harness.py`, `fixtures/`, `runs/`, and the current eval-oriented `tui.py` are supporting research/evaluation artifacts. Preserve useful evidence, but do not optimize the product around the eval harness.
- `.agents/` contains product vision, target architecture, roadmap, eval protocol, conventions, and security guidance.
