# ARCHITECTURE.md — how the harness works

## Components

```
harness.py
├── atelier_chat()      model completions (swap this for your endpoint)
├── store               JSONL of successful actions (load/append)
├── retrieve()          TF-IDF cosine, 0.7 intent + 0.3 environment, top-5
├── BLOCKLIST / blocked()  security gating at store and retrieval time
├── fixtures            pycalc / pytask / nodeblog (+ setup.sh to git-init)
├── TASKS               inspect / search / test / fix + per-repo oracles
├── run_task()          the agent loop for one (arm, repo, task, run)
└── main()              sweeps arms × runs × repos × tasks, writes runs/*.jsonl
```

## The agent loop

The model speaks only in JSON steps:
`{"intent": "<3-8 words>", "command": "<bash>"}` or
`{"intent": "...", "done": true, "answer": "..."}`.
The harness runs the command (120s timeout, whole process-group kill on
timeout so `tail -f | rg` grandchildren can't outlive the shell), appends
the observation, and repeats — max 15 steps, history window capped at 14
messages (system + task prompt always retained).

The two arms are identical except:

- **Control:** no intent requirement, no store, no retrieval.
- **Experimental:** the model must state an intent each step; every
  successful, non-blocklisted command is appended to the store; before each
  step (once the store is non-empty) the top-5 similar past successes are
  injected as "relevant previous successful actions (you may use, modify,
  or ignore them)".

## The store record

```json
{"intent": "...", "command": "...", "cwd_context": "pycalc",
 "environment": {"repo": "pycalc", "top_files": [...], "os": "linux"},
 "environment_text": "pycalc ...", "result_summary": "exit=0, 1.2s, out=...",
 "success": true, "ts": 1234567890.0}
```

Retrieval is lexical in phase 1: TF-IDF vectors over intent text and
environment text, cosine similarity, `0.7 * intent + 0.3 * environment`,
top-5 with score > 0. (No embeddings endpoint was available; lexical
similarity stands in for embedding similarity until phase 2.)

## Oracles (deterministic, external)

| task    | setup (mutation)              | check (independent of the agent)        |
|---------|-------------------------------|------------------------------------------|
| inspect | append comment to a source    | `git status --short` names ⊆ answer      |
| search  | none                          | `rg -n <sym>` files ⊆ answer             |
| test    | none                          | suite passes ⇔ answer says "pass"        |
| fix     | one-line bug planted per repo | suite passes after the run               |

Fixtures are reset with `git checkout -- . && git clean -fdq` before and
after every task. Success is computed by re-running git/rg/the suite —
never by trusting the model's claims.

## Transfer design

- `pycalc` → same project (store warms up here; later runs should benefit)
- `pytask` → similar project (Python/pytest, different domain)
- `nodeblog` → unrelated project (Node; measures retrieval pollution —
  degradation here is the alarm bell)

Run order per arm is fixed: repos pycalc → pytask → nodeblog, tasks in
fixed order, N runs each. The experimental store persists across
everything within an arm, so later tasks can draw on earlier ones.
