# Phase-1 results (2026-10-10, gemma-4-26b-a4b, local)

Full 48-cell dataset: 2 arms x 2 runs x 3 repos x 4 tasks.
(8 nodeblog test/fix cells were invalidated by a broken fixture script,
then re-run on the fixed fixture and merged.)

## Headline

| arm          | success | avg steps | avg failed | wall   | tokens |
|--------------|---------|-----------|------------|--------|--------|
| control      | 20/24   | 4.6       | 0.9        | 2501s  | 127609 |
| experimental | 22/24   | 3.8       | 0.7        | 2516s  | 139497 |

## Learning curve, same project (pycalc)

- experimental run1 -> run2: 5.8 -> 2.2 avg steps (-62%), 4/4 both runs
- control run1 -> run2: 5.0 -> 5.2 avg steps (flat, as expected with no memory)

Repeated rediscovery is eliminated on revisit: the basic effect is established.

## Transfer ladder (avg steps, control -> experimental)

- pycalc (same project):      5.1 -> 4.0, 7/8 -> 8/8
- pytask (similar stack):     5.9 -> 4.4, 6/8 -> 6/8
- nodeblog (unrelated stack): 2.8 -> 3.0, 7/8 -> 8/8

No retrieval pollution observed on the unrelated project. Likely reason: at
this task granularity the learned affordances are mostly stack-agnostic shell
idioms (git status, rg, ls, cat), so they transfer. A stronger pollution test
would need memories that are actively wrong elsewhere (e.g. `cargo test`
memories applied to an npm repo). Note: on nodeblog the experimental arm took
marginally more steps on average but succeeded more often (the fix task ran
longer via retrieved affordances, 8 vs 5 steps, and landed).

## Failure analysis

- 6 of the 8 total failures (both arms) are the `search` task: the agent
  declares done without naming every file that references the symbol.
  Reporting-completeness gap, orthogonal to memory. Both arms suffer it.
- nodeblog `fix` failed 4/4 originally — fixture artifact (see below), not
  an agent result.

## Fixture bug (disclosed, fixed, re-run merged)

nodeblog's package.json had `"test": "node --test tests/"` — the trailing
slash breaks node module resolution, so `npm test` failed on the pristine
fixture. The `test`-task "successes" were agents correctly reporting failure;
the `fix` task was impossible (0/4 systematic failures across both arms).
Fixed to `node --test "tests/*.test.js"` (verified 2 pass / 0 fail), committed
in the fixture repo. The 8 cells were re-run on the fixed fixture and merged:
nodeblog fix is now 4/4 (was 0/4), and the agents' earlier workaround
(invoking `node --test tests/posts.test.js` directly, captured in the store)
is confirmed as genuine problem-solving, not noise.

## Method notes

- Retrieval: TF-IDF cosine over intent+environment text (0.7/0.3); lexical
  stand-in for embeddings (no embeddings endpoint on atelier).
- Store: 94 experiences accumulated by the experimental arm (33 distinct
  commands; the append-only episodic store repeats commands across steps/runs).
- Harness bugs fixed during validation: stdin pipe hangs (rg reading inherited
  stdin), pipeline grandchildren outliving the shell (process groups + killpg).
- Done-without-success (agent declared done, oracle failed; EVAL.md counts
  these separately): control 4, experimental 2 — all the `search` task.
- VM was replaced mid-run (46/48); resumed the last 2 cells from the
  surviving store file.
