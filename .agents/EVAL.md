# EVAL.md — supporting evaluation protocol

## Role of evaluation

Tracer is an interactive terminal agent CLI. This document describes the controlled evaluation used to measure its learned-affordance mechanism. The eval is **supporting infrastructure**, not the product architecture or user experience.

As the product runtime is extracted, the eval should consume the same agent-loop, Bash, memory, retrieval, environment, and safety components that the interactive CLI uses. Fixture tasks, treatment/control arms, setup mutations, and deterministic oracles remain eval-only.

## What counts as signal

For the existing Phase-1-style comparison, a treatment is promising if, across the full cell grid (arms × runs × repos × tasks), the memory-enabled arm improves **task success** and/or **Bash steps** without unacceptable regression in **failed steps**, cost, or unrelated-project transfer. Token cost and wall time are reported alongside; apparent gains should not hide their price.

Phase-1 numbers (48/48 cells, `google/gemma-4-26b-a4b`):

| metric             | experimental | control |
|--------------------|--------------|---------|
| tasks succeeded    | 22/24        | 20/24   |
| avg bash steps     | 3.8          | 4.6     |
| tokens             | ~9% more     | —       |
| wall time          | no win       | —       |
| unrelated transfer | neutral      | —       |

These results are evidence that the mechanism is worth developing, not a specification for the interactive CLI.

## Running the current eval

```bash
bash fixtures/setup.sh
python3 harness.py --arms both --runs 2 --model <model> [--repos ...] [--tasks ...]
```

- Run **both arms** in the same invocation for comparative claims unless debugging one arm.
- `--runs 2` is the current minimum for a claim; single runs are anecdotes.
- Model temperature is 0.2 in the Phase-1 harness. Reasoning models need sufficient output budget.
- Keep the baseline reproducible so product/runtime changes can be compared against prior behavior.

## Reading results

Each line of `runs/run-<ts>.jsonl` is one eval cell:

```text
{arm, repo, task, run, success, steps, failed_steps,
 prompt_tokens, completion_tokens, wall_s, done}
```

Aggregate by arm first, then inspect transfer by repo and behavior by task.

`success` is the oracle's verdict, not the model's. `done` without `success` means the agent believed it finished but did not satisfy the independent check.

## Determinism notes

- Fixture reset is via git; `fixtures/setup.sh` must have run once.
- Existing Phase-1 task order is fixed so stores warm comparably across arms.
- The model is a major uncontrolled variable. Comparative runs should use the same model/configuration as closely as possible.
- Preserve published Phase-1 artifacts rather than silently rewriting historical results.

## Adding eval coverage

A new task family needs a prompt, setup mutation (or none), and an independent oracle. A new fixture needs a small runnable repository and enough metadata to support the selected task families. Keep fixtures small so evaluation remains inexpensive.

Do not add benchmark-specific requirements to the production runtime merely to make an oracle easier. If the eval needs adapters around the product runtime, keep those adapters in eval code.

## Product-facing eval goals

As the interactive CLI matures, add evaluations for the behaviors that matter to real use:

- whether retrieved affordances reduce rediscovery in the same workspace,
- whether useful behavior transfers to structurally similar repositories,
- whether unrelated memories pollute action selection,
- whether retrieval remains useful after many sessions and a large store,
- whether intent-before-retrieval outperforms task-prompt-only retrieval,
- whether derived templates/prototypes outperform raw episodes,
- whether memory improves outcomes enough to justify token, latency, and storage cost.
