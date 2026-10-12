#!/usr/bin/env python3
"""Tracer TUI — terminal frontend for the phase-1 eval harness.

A viewer/controller over the harness JSONL result contract (see EVAL.md):
it never imports harness internals, so it runs wherever the results file
does. Two live modes plus a headless one:

  watch   python3 tui.py --file runs/run-<ts>.jsonl
  run     python3 tui.py --runs 2 --arms both --model <m>   # spawns harness.py
  print   python3 tui.py --file runs/run-<ts>.jsonl --print  # no curses

Keys: q quit · t toggle summary · left/right change run · r re-run · p pause.
"""
import argparse
import curses
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ("control", "experimental")
TASK_ORDER = ["inspect", "search", "test", "fix"]
REPO_ORDER = ["pycalc", "pytask", "nodeblog"]
POLL_S = 0.5

# ------------------------------------------------------------------ data

def load_cells(path):
    """Read a results JSONL into {(arm,run,repo,task): cell}. Tolerant of a
    partial trailing line while the harness is still writing."""
    cells = {}
    if not path or not os.path.exists(path):
        return cells
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            cells[(r.get("arm"), r.get("run"), r.get("repo"), r.get("task"))] = r
    return cells


def order(universe, preferred):
    present = set(universe)
    out = [x for x in preferred if x in present]
    out += sorted(x for x in present if x not in preferred)
    return out


def dims(cells, repos, tasks, runs):
    repos = order({k[2] for k in cells if k[2]}, REPO_ORDER) if repos is None \
        else [r for r in repos.split(",") if r]
    tasks = order({k[3] for k in cells if k[3]}, TASK_ORDER) if tasks is None \
        else [t for t in tasks.split(",") if t]
    runs = sorted({k[1] for k in cells if k[1] is not None}) if runs is None \
        else list(range(1, runs + 1))
    return repos, tasks, runs


def agg_arm(cells, arm):
    c = [r for r in cells.values() if r.get("arm") == arm]
    n = len(c)
    if not n:
        return None
    return dict(
        n=n,
        succ=sum(1 for r in c if r.get("success")),
        steps=sum(r.get("steps", 0) for r in c) / n,
        failed=sum(r.get("failed_steps", 0) for r in c) / n,
        tok=sum(r.get("prompt_tokens", 0) + r.get("completion_tokens", 0) for r in c),
        wall=sum(r.get("wall_s", 0) for r in c),
    )


def agg_cell(cells, arm, run, repo, task):
    return cells.get((arm, run, repo, task))


def agg_repo(cells, arm, repo):
    c = [r for r in cells.values()
         if r.get("arm") == arm and r.get("repo") == repo]
    n = len(c)
    if not n:
        return None
    return dict(n=n, succ=sum(1 for r in c if r.get("success")),
                steps=sum(r.get("steps", 0) for r in c) / n)


def agg_task(cells, arm, task):
    c = [r for r in cells.values()
         if r.get("arm") == arm and r.get("task") == task]
    n = len(c)
    if not n:
        return None
    return dict(n=n, succ=sum(1 for r in c if r.get("success")))


# ------------------------------------------------------------------ print

def render_print(cells, repos, tasks, runs):
    """Plain-text summary — the same aggregation the curses view uses, for
    headless assertion and piping."""
    lines = []
    lines.append("TRACER  results  (%d cells)" % len(cells))
    lines.append("")
    lines.append("%-14s %6s %6s %7s %9s %8s" %
                 ("arm", "succ", "steps", "failed", "tokens", "wall"))
    for arm in ARMS:
        a = agg_arm(cells, arm)
        if not a:
            continue
        lines.append("%-14s %4d/%-2d %6.2f %7.2f %9d %7.0fs" %
                     (arm, a["succ"], a["n"], a["steps"], a["failed"],
                      a["tok"], a["wall"]))
    lines.append("")
    lines.append("transfer ladder (avg steps, succ/n)")
    lines.append("%-10s %10s %10s" % ("repo", "control", "experim."))
    for repo in repos:
        c = agg_repo(cells, "control", repo)
        e = agg_repo(cells, "experimental", repo)
        cs = "%.1f %d/%d" % (c["steps"], c["succ"], c["n"]) if c else "-"
        es = "%.1f %d/%d" % (e["steps"], e["succ"], e["n"]) if e else "-"
        lines.append("%-10s %10s %10s" % (repo, cs, es))
    lines.append("")
    lines.append("by task (succ/n)")
    lines.append("%-10s %10s %10s" % ("task", "control", "experim."))
    for task in tasks:
        c = agg_task(cells, "control", task)
        e = agg_task(cells, "experimental", task)
        cs = "%d/%d" % (c["succ"], c["n"]) if c else "-"
        es = "%d/%d" % (e["succ"], e["n"]) if e else "-"
        lines.append("%-10s %10s %10s" % (task, cs, es))
    return "\n".join(lines)


# ------------------------------------------------------------------ curses

def _glyph(cell):
    """Single-width ASCII glyph — avoids curses wide-character drift.

    "O" success, "X" fail, "." pending."""
    if cell is None:
        return ".", curses.A_DIM
    if cell.get("success"):
        return "O", curses.color_pair(2)
    return "X", curses.color_pair(3)


def _safe_add(win, y, x, s, attr=0):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    win.addnstr(y, x, s, max(0, w - x - 1), attr)


def draw_matrix(scr, cells, repos, tasks, run, show_summary):
    if show_summary:
        draw_summary(scr, cells, repos, tasks)
        return
    _safe_add(scr, 1, 0, " RUN %s   (left/right change run - t summary)" % run,
              curses.color_pair(1) | curses.A_BOLD)
    cw = 8
    # header row of task names, one 8-col cell per task. The low 7 cols hold
    # control/gap/exp; the 8th is a trailing gutter so a 7-col name like
    # "inspect" never abuts the next column.
    for j, task in enumerate(tasks):
        _safe_add(scr, 2, 10 + j * cw, task.ljust(8), curses.A_BOLD)
    for i, repo in enumerate(repos):
        row = 3 + i
        _safe_add(scr, row, 0, repo[:8].ljust(8), curses.A_BOLD)
        for j, task in enumerate(tasks):
            col = 10 + j * cw
            for k, arm in enumerate(ARMS):
                cell = agg_cell(cells, arm, run, repo, task)
                g, attr = _glyph(cell)
                steps = "" if cell is None else str(cell.get("steps", ""))
                tok = "%s%s" % (g, steps)      # e.g. "O2" or "X11"
                # control in cols [0,4), exp in [4,7)
                _safe_add(scr, row, col + k * 4, tok.ljust(3), attr)
    _safe_add(scr, 3 + len(repos) + 1, 0,
              "cell = control then experimental:  O success  X fail  . pending",
              curses.A_DIM)


def draw_summary(scr, cells, repos, tasks):
    _safe_add(scr, 1, 0, " SUMMARY   (t back to matrix)",
              curses.color_pair(1) | curses.A_BOLD)
    _safe_add(scr, 2, 0, "%-14s %6s %6s %7s %9s %8s" %
              ("arm", "succ", "steps", "failed", "tokens", "wall"), curses.A_BOLD)
    r = 3
    for arm in ARMS:
        a = agg_arm(cells, arm)
        if not a:
            continue
        _safe_add(scr, r, 0, "%-14s %4d/%-2d %6.2f %7.2f %9d %7.0fs" %
                  (arm, a["succ"], a["n"], a["steps"], a["failed"], a["tok"],
                   a["wall"]))
        r += 1
    r += 1
    _safe_add(scr, r, 0, "transfer ladder (avg steps, succ/n)", curses.A_BOLD)
    r += 1
    _safe_add(scr, r, 0, "%-10s %12s %12s" % ("repo", "control", "experim."),
              curses.A_BOLD)
    r += 1
    for repo in repos:
        c = agg_repo(cells, "control", repo)
        e = agg_repo(cells, "experimental", repo)
        cs = "%.1f %d/%d" % (c["steps"], c["succ"], c["n"]) if c else "-"
        es = "%.1f %d/%d" % (e["steps"], e["succ"], e["n"]) if e else "-"
        _safe_add(scr, r, 0, "%-10s %12s %12s" % (repo, cs, es))
        r += 1
    r += 1
    _safe_add(scr, r, 0, "by task (succ/n)", curses.A_BOLD)
    r += 1
    _safe_add(scr, r, 0, "%-10s %12s %12s" % ("task", "control", "experim."),
              curses.A_BOLD)
    r += 1
    for task in tasks:
        c = agg_task(cells, "control", task)
        e = agg_task(cells, "experimental", task)
        cs = "%d/%d" % (c["succ"], c["n"]) if c else "-"
        es = "%d/%d" % (e["succ"], e["n"]) if e else "-"
        _safe_add(scr, r, 0, "%-10s %12s %12s" % (task, cs, es))
        r += 1


def run_curses(args):
    state = {"proc": None, "out": args.file, "paused": False,
             "err_path": None}

    def spawn():
        out = args.out or os.path.join(HERE, "runs",
                                       "run-tui-%d.jsonl" % int(time.time()))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w").close()
        err_path = out + ".err"
        errf = open(err_path, "w")
        cmd = [sys.executable, os.path.join(HERE, "harness.py"),
               "--arms", args.arms, "--runs", str(args.runs),
               "--model", args.model, "--repos", args.repos,
               "--tasks", args.tasks, "--out", out]
        p = subprocess.Popen(cmd, cwd=HERE, stdout=errf,
                             stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        state.update(proc=p, out=out, err_path=err_path, paused=False)

    if not args.file:
        spawn()

    def loop(scr):
        curses.curs_set(0)
        scr.nodelay(True)
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_RED, -1)
        repos, tasks, runs = dims(load_cells(state["out"]),
                                  None if args.file else args.repos,
                                  None if args.file else args.tasks,
                                  None if args.file else args.runs)
        run_idx = 0
        show_summary = False
        last = 0.0
        while True:
            k = scr.getch()
            if k in (ord("q"), 27):
                break
            if k == ord("t"):
                show_summary = not show_summary
            elif k in (curses.KEY_LEFT,) and runs:
                run_idx = (run_idx - 1) % len(runs)
            elif k in (curses.KEY_RIGHT,) and runs:
                run_idx = (run_idx + 1) % len(runs)
            elif k == ord("r") and not args.file:
                if state["proc"] and state["proc"].poll() is None:
                    state["proc"].terminate()
                spawn()
            elif k == ord("p") and state["proc"] and state["proc"].poll() is None:
                import signal
                sig = signal.SIGSTOP if state["paused"] else signal.SIGCONT
                try:
                    os.killpg(os.getpgid(state["proc"].pid), sig)
                except Exception:
                    pass
                state["paused"] = not state["paused"]
            if time.time() - last >= POLL_S:
                last = time.time()
                scr.erase()
                cells = load_cells(state["out"])
                if not repos:
                    repos, tasks, runs = dims(cells, None, None, None)
                if not runs:
                    runs = [1]
                h, w = scr.getmaxyx()
                _safe_add(scr, 0, 0, "TRACER  %s" %
                          ("watch " + os.path.basename(state["out"])
                           if args.file else "run"), curses.A_BOLD)
                _safe_add(scr, 0, max(0, w - 24), "%d cells" % len(cells),
                          curses.A_DIM)
                if show_summary:
                    draw_summary(scr, cells, repos, tasks)
                else:
                    draw_matrix(scr, cells, repos, tasks,
                                runs[run_idx] if runs else 1, False)
                p = state["proc"]
                if p is not None:
                    status = ("paused" if state["paused"] else
                              "running" if p.poll() is None else "exited")
                    _safe_add(scr, h - 1, 0,
                              "harness %s · q quit · r re-run · p pause" % status,
                              curses.color_pair(1))
                    if p.poll() is not None and not cells and state["err_path"]:
                        tail = open(state["err_path"]).read().strip().splitlines()[-6:]
                        for i, ln in enumerate(tail):
                            _safe_add(scr, 6 + i, 0, ln[:w - 1], curses.color_pair(3))
                else:
                    _safe_add(scr, h - 1, 0,
                              "q quit · t summary · ←/→ run", curses.color_pair(1))
                scr.refresh()
            time.sleep(0.05)

    try:
        curses.wrapper(loop)
    finally:
        p = state["proc"]
        if p and p.poll() is None:
            p.terminate()


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description="Tracer eval-harness TUI")
    ap.add_argument("--file", help="watch an existing results JSONL")
    ap.add_argument("--print", action="store_true", dest="do_print",
                    help="print the summary and exit (no curses)")
    ap.add_argument("--out", default=None, help="results path for run mode")
    ap.add_argument("--arms", default="both",
                    choices=["both", "control", "experimental"])
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--model", default="google/gemma-4-26b-a4b")
    ap.add_argument("--repos", default="pycalc,pytask,nodeblog")
    ap.add_argument("--tasks", default="inspect,search,test,fix")
    args = ap.parse_args()

    if args.file:
        cells = load_cells(args.file)
        repos, tasks, runs = dims(cells, None, None, None)
        if args.do_print:
            print(render_print(cells, repos, tasks, runs))
            return
        run_curses(args)
    else:
        if args.do_print:
            ap.error("--print requires --file")
        run_curses(args)


if __name__ == "__main__":
    main()
