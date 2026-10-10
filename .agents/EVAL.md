# EVAL.md — the eval protocol

## What counts as signal

A phase passes if, across the full cell grid (arms × runs × repos ×
tasks), the experimental arm beats control on **task success** and
**bash steps** without regressing on **failed steps**, and without
degrading the unrelated-project transfer cell. Token cost and wall time
are reported alongside — a win that hides its price is not a win
(see VISION.md).

Phase-1 numbers (48/48 cells, `google/gemma-4-26b-a4b`):

| metric            | experimental | control |
|-------------------|--------------|---------|
| tasks succeeded   | 22/24        | 20/24   |
| avg bash steps    | 3.8          | 4.6     |
| tokens            | ~9% more     | —       |
| wall time         | no win       | —       |
| unrelated transfer| neutral      | —       |

## Running an eval

```bash
bash fixtures/setup.sh
python3 harness.py --arms both --runs 2 --model <model> [--repos ...] [--tasks ...]
```

- Always run **both arms** in the same invocation unless you're debugging
  one arm; the comparison is the experiment.
- `--runs 2` is the minimum for a claim; single runs are anecdotes.
- Model temperature is 0.2 in the harness; don't raise it for "fairness"
  without saying so. Reasoning models need `max_tokens >= 1024`.

## Reading results

Each line of `runs/run-<ts>.jsonl` is one cell:
`{arm, repo, task, run, success, steps, failed_steps, prompt_tokens,
completion_tokens, wall_s, done}`. Aggregate by arm first, then cut by
repo (transfer analysis) and by task (where does memory help most?).

`success` is the oracle's verdict, not the model's. `done` without
`success` means the agent *thought* it finished — that's a distinct
failure worth counting separately.

## Determinism notes

- Fixture reset is via git; `fixtures/setup.sh` must have run once.
- Task order is fixed (not shuffled) so stores warm up comparably
  across arms. Don't randomize order without a reason and a note.
- The model is the largest uncontrolled variable. Same model, same
  day, both arms — or the comparison is confounded.

## Adding a task family or fixture

A new task needs: a `prompt`, a `setup` mutation (or none), and a `check`
oracle that re-derives the answer independently. A new fixture needs: a
small real repo with a runnable suite, an entry in `REPO_TASK`
(symbol + source path), and a `_plant_bug` branch if it should support
`fix`. Keep fixtures tiny — eval speed is a feature.
