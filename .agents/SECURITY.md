# SECURITY.md — security model (non-negotiable)

## Threat model

The harness executes model-chosen bash commands. The model is untrusted
input to the shell. Everything below exists because of that sentence.

## Current mitigations

1. **Fixture-scoped cwd.** Commands start in the fixture repo for the
   current task. This is a working directory, **not a sandbox** — a shell
   command can still reach absolute paths, `~`, or `../`. The blocklist and
   human supervision bound the blast radius, not the cwd. Never point the
   harness at a non-fixture directory.
2. **Blocklist, twice.** `BLOCKLIST` patterns (destructive ops like
   `rm -rf /`, `mkfs`, `dd … of=/dev`, fork bombs, `curl|sh` pipes,
   credential-shaped literals, `.ssh/` / `.aws/` paths) are enforced at
   **store time** (never learn a dangerous action) and at
   **retrieval time** (never suggest one). The list only grows; weakening
   it is a security-relevant change requiring a documented reason.
3. **Timeouts + process-group kill.** 120s per command; on timeout the
   whole process group is SIGKILLed so pipeline grandchildren
   (e.g. `tail -f | rg`) can't outlive the shell.
4. **No secrets in the loop.** The harness carries no credentials except
   the model-endpoint surrogate, which never enters the store or the
   agent's context. Credential-shaped command literals are blocklisted
   from storage.
5. **Retrieval is never permission.** Retrieved affordances are text in
   a prompt. The agent may ignore them; the harness never auto-executes
   them.
6. **Human-supervised runs.** The harness is run locally by a human who
   can see what it's doing. There is no autonomous deployment story,
   and adding one requires a new security review, not a flag.

## Rules for contributors

- Don't weaken `BLOCKLIST`, raise `CMD_TIMEOUT`, or widen the cwd
  without documenting why in the commit.
- Don't add network access to fixtures or the agent loop.
- Don't store or log anything credential-shaped, even redacted-looking.
- If you find a bypass (a dangerous command the blocklist misses),
  fix the blocklist first, report it in the commit, and re-run the
  eval — a bypass invalidates prior safety claims.
