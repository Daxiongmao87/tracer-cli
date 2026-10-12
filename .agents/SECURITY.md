# SECURITY.md — security model

## Threat model

Tracer executes model-chosen shell commands. Model output, retrieved memory, repository contents, command output, and user-provided text can all influence those commands and must be treated as untrusted input at the execution boundary.

Retrieval is **never permission to execute**. A command becoming familiar or highly ranked must not bypass whatever approval/policy would apply if the model had generated it from scratch.

## Current Phase-1 eval restrictions

The existing `harness.py` is experimental scaffolding and is not hardened for arbitrary user workspaces.

1. **Fixture-only use.** Commands start in the current fixture repository. A cwd is not a sandbox: shell commands can still reach absolute paths, `~`, `../`, devices, and the network. Keep the current eval harness pointed only at disposable fixture repositories.
2. **Blocklist at store and retrieval.** Existing destructive/credential-shaped patterns are checked before an episode is stored and again before it is suggested. This reduces obvious risk but is not a production sandbox or complete command policy.
3. **Timeouts + process-group kill.** Commands have bounded execution time and timed-out process groups are killed.
4. **No credential capture.** Model-provider credentials must not enter prompts, observations, memory records, or command history.
5. **Human supervision.** The current eval is intended to be observed locally.

These restrictions protect the proof of concept. Do not interpret them as the final product security design.

## Product security requirements

The interactive Tracer CLI is intended to operate in real user-selected working directories, so it requires a stronger explicit execution policy than the current eval harness.

At minimum, product design must preserve these principles:

- **Workspace boundary awareness.** Tracer must know the active workspace and distinguish ordinary in-workspace operations from access outside it.
- **Consequence-based approval.** Potentially destructive, privileged, secret-bearing, external-network, or out-of-workspace actions require appropriate policy/approval rather than relying only on regex matching.
- **No trust escalation from memory.** Retrieved affordances receive the same safety treatment as newly generated commands.
- **Secret hygiene.** Credentials and secret-shaped values must be redacted or excluded from durable episodic memory. Environment fingerprints must not casually serialize the user's environment variables or credential files.
- **Bounded execution.** Timeouts, process cleanup, output limits, and cancellation remain first-class runtime behavior.
- **Visible user control.** Interactive sessions must permit interruption and must make consequential actions understandable before execution when approval is required.
- **Provider isolation.** Model-provider authentication stays outside model-visible context and learned memory.
- **Prompt/repository injection resistance at the execution boundary.** Instructions discovered in files or command output cannot themselves grant execution authority.

Whether the production implementation uses OS sandboxing, namespaces/containers, filesystem policy, an approval engine, or a combination should be decided during implementation. Do not claim the current blocklist provides those guarantees.

## Learned-memory-specific risks

Memory introduces additional failure modes:

- a previously safe command can become unsafe in a different workspace;
- a command can accidentally contain a literal secret or identifying path;
- poisoned repository content can influence an episode that is later retrieved elsewhere;
- repeated retrieval can amplify a mediocre or unsafe behavior merely because it is familiar;
- generalized templates can broaden the scope of an action beyond the examples that created them.

Mitigations should therefore include context-aware retrieval, sanitization/redaction before storage, risk re-evaluation at execution time, provenance for derived affordances, and the ability to decay/delete bad memories.

## Rules for contributors

- Do not weaken the current eval's safety checks merely to improve benchmark numbers.
- Do not reuse the fixture-only safety model unchanged for the interactive product.
- Security-relevant changes to command execution, approval, memory sanitization, credentials, networking, cwd/workspace handling, or timeouts must be called out explicitly in the commit.
- If a dangerous stored/retrieved action can bypass execution policy, fix the execution boundary first; filtering the memory store alone is not sufficient.
