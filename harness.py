#!/usr/bin/env python3
"""Phase-1 affordance-cache experiment harness.

Two arms, identical except:
  control:      bash only. No intent requirement, no memory.
  experimental: bash + short intent each step + successful actions stored as
                {intent, command, cwd_context, environment, result_summary}
                + top-5 similar past successes retrieved before each call.

No taxonomy, no clustering, no templates, no AST normalization in phase 1.
Retrieval = TF-IDF cosine over (intent, environment) text, 0.7/0.3 weighting.
Usage: harness.py --arms both --runs 2 --model qwen/qwen3.8-flash-next
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response
import urllib.request

BASE = "https://atelier.astralkeep.com/v1"
ALLOWED = ("atelier.astralkeep.com",)
CRED = "custom.atelier"
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures")

MAX_STEPS = 15
CMD_TIMEOUT = 120
OBS_TRUNC = 3000

# ---------------------------------------------------------------- atelier

def atelier_chat(messages, model, max_tokens=2048, temperature=0.2):
    payload = {"model": model, "messages": messages,
               "temperature": temperature, "max_tokens": max_tokens}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + "/chat/completions", data=data,
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
    with urllib.request.urlopen(req, timeout=180) as resp:
        out = read_json_response(resp)
    msg = out["choices"][0]["message"]["content"]
    usage = out.get("usage", {}) or {}
    return msg, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)

# ---------------------------------------------------------------- store

BLOCKLIST = [
    r"rm\s+-rf\s+/(?!\s*$)", r"\bmkfs\b", r"\bdd\s+.*\bof=/dev",
    r":\(\)\s*\{", r"\bcurl\b.*\|\s*(ba)?sh",
    r"(password|passwd|secret|api[_-]?key|token)\s*=\s*\S+",
    r"\.ssh/", r"\.aws/",
]

def blocked(cmd):
    return any(re.search(p, cmd, re.I) for p in BLOCKLIST)

def load_store(path):
    if not os.path.exists(path):
        return []
    recs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs

def append_store(path, rec):
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")

# ------------------------------------------------------- retrieval (tf-idf)

def _toks(s):
    return re.findall(r"[a-z0-9_]{2,}", (s or "").lower())

def _idf(docs):
    df = Counter()
    for d in docs:
        for t in set(_toks(d)):
            df[t] += 1
    n = max(len(docs), 1)
    return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}

def _vec(s, idf):
    v = Counter(_toks(s))
    return {t: (c * idf.get(t, 1.0)) for t, c in v.items()}

def _cos(a, b):
    if not a or not b:
        return 0.0
    dot = sum(a[t] * b.get(t, 0.0) for t in a)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0

def retrieve(store, intent_query, env_query, k=5):
    """0.7 * intent similarity + 0.3 * environment similarity."""
    docs_i = [r["intent"] for r in store]
    docs_e = [r["environment_text"] for r in store]
    idf_i, idf_e = _idf(docs_i), _idf(docs_e)
    qv_i, qv_e = _vec(intent_query, idf_i), _vec(env_query, idf_e)
    scored = []
    for r in store:
        si = _cos(qv_i, _vec(r["intent"], idf_i))
        se = _cos(qv_e, _vec(r["environment_text"], idf_e))
        scored.append((0.7 * si + 0.3 * se, r))
    scored.sort(key=lambda x: -x[0])
    # Blocklist is enforced here too (SECURITY.md: "twice"). It only grows, so
    # an entry stored under an older list can match a later pattern; filtering
    # at retrieval keeps a stored action from ever being suggested.
    return [(s, r) for s, r in scored[:k] if s > 0 and not blocked(r["command"])]

# ---------------------------------------------------------------- fixtures

def env_fingerprint(repo_path, repo_id):
    top = sorted(os.listdir(repo_path))[:24]
    env = {"repo": repo_id, "top_files": top, "os": "linux"}
    env_text = repo_id + " " + " ".join(top)
    return env, env_text

def reset_repo(path):
    subprocess.run(["git", "checkout", "--", "."], cwd=path,
                   capture_output=True, stdin=subprocess.DEVNULL)
    subprocess.run(["git", "clean", "-fdq"], cwd=path, capture_output=True,
                   stdin=subprocess.DEVNULL)

PYTEST = ["python3", "-m", "pytest", "-q"]

TASKS = {
    "inspect": {
        "prompt": ("This repository has uncommitted local changes. "
                   "Report exactly which files have been modified, added, or deleted."),
        "setup": lambda p: open(os.path.join(p, _first_src(p)), "a").write("\n# local tweak\n"),
        "check": lambda p, ans: _check_names(p, ans),
    },
    "search": {
        "prompt": ("Find every reference to the symbol '{sym}' in this repository's "
                   "source and tests. Report each file and line number."),
        "setup": lambda p: None,
        "check": lambda p, ans: _check_search(p, ans),
    },
    "test": {
        "prompt": ("Run this repository's test suite using its own configured "
                   "test command. Report whether the suite passes or fails."),
        "setup": lambda p: None,
        "check": lambda p, ans: _check_test(p, ans),
    },
    "fix": {
        "prompt": ("This repository's test suite currently has a failing test. "
                   "Find the bug, fix it, and confirm the suite passes."),
        "setup": lambda p: _plant_bug(p),
        "check": lambda p, ans: _suite_passes(p),
    },
}

REPO_TASK = {
    "pycalc":   {"sym": "mul",      "src": "pycalc/__init__.py"},
    "pytask":   {"sym": "complete", "src": "pytask/__init__.py"},
    "nodeblog": {"sym": "slugify",  "src": "src/posts.js"},
}

def _first_src(p):
    repo = os.path.basename(p)
    return REPO_TASK[repo]["src"]

def _check_names(p, ans):
    out = subprocess.run(["git", "status", "--short"], cwd=p,
                         capture_output=True, text=True,
                         stdin=subprocess.DEVNULL).stdout
    changed = [l[3:].strip().strip('"') for l in out.splitlines() if l.strip()]
    if not changed:
        return False
    a = (ans or "").lower()
    return all(c.lower() in a for c in changed)

def _check_search(p, ans):
    repo = os.path.basename(p)
    sym = REPO_TASK[repo]["sym"]
    out = subprocess.run(["rg", "-n", sym], cwd=p,
                         capture_output=True, text=True,
                         stdin=subprocess.DEVNULL).stdout
    files = sorted(set(l.split(":")[0] for l in out.splitlines() if l.strip()))
    if not files:
        return False
    a = (ans or "").lower()
    return sym.lower() in a and all(f.lower() in a for f in files)

def _suite_passes(p):
    repo = os.path.basename(p)
    if repo == "nodeblog":
        cmd = ["npm", "test", "--silent"]
    else:
        cmd = PYTEST
    r = subprocess.run(cmd, cwd=p, capture_output=True, text=True, timeout=180,
                       stdin=subprocess.DEVNULL)
    return r.returncode == 0

def _check_test(p, ans):
    passes = _suite_passes(p)
    a = (ans or "").lower()
    return ("pass" in a) if passes else ("fail" in a)

def _plant_bug(p):
    repo = os.path.basename(p)
    if repo == "pycalc":
        fp = os.path.join(p, "pycalc/__init__.py")
        s = open(fp).read().replace("return a * b", "return a * b + 1")
        open(fp, "w").write(s)
    elif repo == "pytask":
        fp = os.path.join(p, "pytask/__init__.py")
        s = open(fp).read().replace("it[\"done\"] = True", "it[\"done\"] = False")
        open(fp, "w").write(s)
    elif repo == "nodeblog":
        fp = os.path.join(p, "src/posts.js")
        s = open(fp).read().replace('.replace(/\\s+/g, "-")', '.replace(/\\s+/g, "_")')
        open(fp, "w").write(s)

# ---------------------------------------------------------------- agent loop

SYSTEM = ("You are a terminal agent. You can ONLY run bash commands, one per step. "
          "Reply with exactly one JSON object and no other text.\n"
          '{"intent": "<what you are trying to do, 3-8 words>", "command": "<bash command>"}\n'
          "When the task is complete, reply:\n"
          '{"intent": "<final summary>", "done": true, "answer": "<final answer>"}\n'
          "Rules: commands run in the task directory shown in the prompt. "
          "Do not repeat a command that already failed. Prefer git, rg, pytest, node/npm.")

def _parse_step(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

def run_command(cmd, cwd):
    """Run cmd; on timeout kill the whole process group so pipeline
    grandchildren (e.g. `tail -f | rg`) can't outlive the shell."""
    import signal as _signal
    t0 = time.time()
    p = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        out, _ = p.communicate(timeout=CMD_TIMEOUT)
        return p.returncode, (out or "")[:OBS_TRUNC], time.time() - t0
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, _signal.SIGKILL)
        except Exception:
            pass
        try:
            p.wait(timeout=5)
        except Exception:
            pass
        return 124, f"<timed out after {CMD_TIMEOUT}s>", CMD_TIMEOUT

def run_task(arm, repo_id, task_name, model, store_path, run_idx):
    repo_path = os.path.join(FIX, repo_id)
    reset_repo(repo_path)
    task = TASKS[task_name]
    task["setup"](repo_path)
    prompt = task["prompt"]
    if "{sym}" in prompt:
        prompt = prompt.format(sym=REPO_TASK[repo_id]["sym"])
    prompt = f"Task directory: {repo_path}\nTask: {prompt}"

    env, env_text = env_fingerprint(repo_path, repo_id)
    store = load_store(store_path) if arm == "experimental" else []

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt}]
    steps, failed = 0, 0
    ptok, ctok = 0, 0
    answer, done = None, False
    last_obs = ""
    t_start = time.time()
    commands = []

    for _ in range(MAX_STEPS):
        if arm == "experimental" and store:
            query = prompt + "\n" + (last_obs[:500] if steps else "")
            hits = retrieve(store, query, env_text, k=5)
            if hits:
                aff = "\n".join(
                    f"- {r['intent']}\n  {r['command']}" for _, r in hits)
                messages.append({
                    "role": "user",
                    "content": ("Relevant previous successful actions "
                                "(you may use, modify, or ignore them):\n" + aff)})
        try:
            text, p, c = atelier_chat(messages, model)
        except Exception as e:
            last_obs = f"<model error: {e}>"
            messages.append({"role": "user", "content": last_obs})
            continue
        ptok += p
        ctok += c
        step = _parse_step(text)
        messages.append({"role": "assistant", "content": text})
        if not step:
            last_obs = "<harness: could not parse JSON, reply with exactly one JSON object>"
            messages.append({"role": "user", "content": last_obs})
            continue
        if step.get("done"):
            answer, done = step.get("answer", ""), True
            break
        cmd = step.get("command", "")
        intent = step.get("intent", "")
        if not cmd:
            last_obs = "<harness: empty command>"
            messages.append({"role": "user", "content": last_obs})
            continue
        code, out, dur = run_command(cmd, repo_path)
        steps += 1
        commands.append(cmd)
        if code != 0:
            failed += 1
        last_obs = f"exit={code} ({dur:.1f}s)\n{out}"
        messages.append({"role": "user", "content": last_obs})
        # keep history bounded; always retain system + task prompt
        if len(messages) > 14:
            messages = messages[:2] + messages[-12:]
        if arm == "experimental" and code == 0 and not blocked(cmd):
            rel = os.path.relpath(repo_path, FIX)
            append_store(store_path, {
                "intent": intent, "command": cmd,
                "cwd_context": rel,
                "environment": env, "environment_text": env_text,
                "result_summary": f"exit=0, {dur:.1f}s, out={out[:200]}",
                "success": True, "ts": time.time(),
            })
            store = load_store(store_path)

    wall = time.time() - t_start
    success = False
    if done:
        try:
            success = bool(task["check"](repo_path, answer))
        except Exception:
            success = False
    reset_repo(repo_path)
    return {"arm": arm, "repo": repo_id, "task": task_name, "run": run_idx,
            "success": success, "steps": steps, "failed_steps": failed,
            "prompt_tokens": ptok, "completion_tokens": ctok,
            "wall_s": round(wall, 1), "done": done}

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="both", choices=["both", "control", "experimental"])
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--model", default="google/gemma-4-26b-a4b")
    ap.add_argument("--repos", default="pycalc,pytask,nodeblog")
    ap.add_argument("--tasks", default="inspect,search,test,fix")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    arms = ["control", "experimental"] if args.arms == "both" else [args.arms]
    repos = args.repos.split(",")
    tasks = args.tasks.split(",")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = args.out or os.path.join(HERE, "runs", f"run-{ts}.jsonl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    results = []
    for arm in arms:
        store_path = os.path.join(HERE, "runs", f"store-{arm}-{ts}.jsonl")
        open(store_path, "w").close()
        for run_idx in range(1, args.runs + 1):
            for repo in repos:
                for tname in tasks:
                    print(f"[{arm} run{run_idx}] {repo}/{tname} ...", flush=True)
                    try:
                        r = run_task(arm, repo, tname, args.model, store_path, run_idx)
                    except Exception as e:
                        r = {"arm": arm, "repo": repo, "task": tname,
                             "run": run_idx, "success": False, "error": str(e)}
                    results.append(r)
                    with open(out_path, "a") as f:
                        f.write(json.dumps(r) + "\n")
                    print(f"   -> success={r.get('success')} steps={r.get('steps')} "
                          f"failed={r.get('failed_steps')} wall={r.get('wall_s')}s "
                          f"tok={r.get('prompt_tokens',0)+r.get('completion_tokens',0)}",
                          flush=True)
    print(f"\nwrote {out_path}")

if __name__ == "__main__":
    main()
