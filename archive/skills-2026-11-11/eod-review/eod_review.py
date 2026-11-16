#!/usr/bin/env python3
"""EOD review engine: commits + Claude Code token usage for a work unit.

A "work unit" is resolved from (in priority order) explicit flags, a named unit
in units.json, then sensible defaults (current worktree + current branch + today).

Token usage is read from Claude Code session transcripts under
~/.claude/projects/<slug>/**/*.jsonl. Every usage-bearing entry carries `cwd`,
`gitBranch`, `timestamp`, `model`, and `usage`, so attribution is exact:
filter by worktree path (cwd) and/or branch (gitBranch), bucketed by local date.

Commits come from `git log` in the worktree. Token attribution is by
worktree+branch (NOT by commit), so it also counts exploration that produced no
commit, which is what an honest EOD review wants.

Cost is an ESTIMATE from an editable price table (pricing.json) and is labelled
as such — never quote it as billed cost.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import hashlib
import sqlite3
import subprocess
import sys

HOME = os.path.expanduser("~")
# Claude Code's own folder; CLAUDE_CONFIG_DIR moves it.
CLAUDE_DIR = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(HOME, ".claude")
PROJECTS_DIR = os.path.join(CLAUDE_DIR, "projects")
CODEX_DIR = os.path.join(HOME, ".codex")
# Grok CLI (xAI). Per-turn token usage is in one rolling log keyed by session id;
# each session's cwd/branch/model come from its summary.json.
GROK_DIR = os.path.join(HOME, ".grok")
GROK_SESSIONS_DIR = os.path.join(GROK_DIR, "sessions")
GROK_LOG = os.path.join(GROK_DIR, "logs", "unified.jsonl")
# Agents read by collect_other_agents(). Token counts where the agent records
# them (Gemini CLI, opencode); session counts where it does not (Cursor,
# Antigravity).
GEMINI_DIR = os.path.join(HOME, ".gemini")
OPENCODE_DB = os.path.join(HOME, ".local", "share", "opencode", "opencode.db")
CURSOR_DB = os.path.join(HOME, "Library", "Application Support", "Cursor", "User",
                         "globalStorage", "state.vscdb")
CURSOR_DB_LINUX = os.path.join(HOME, ".config", "Cursor", "User", "globalStorage", "state.vscdb")
ANTIGRAVITY_DB = os.path.join(GEMINI_DIR, "antigravity", "conversation_summaries.db")
OTHER_AGENTS = ("gemini", "opencode", "cursor", "antigravity")
# Agent orchestrators (Superconductor, Conductor) check worktrees out OUTSIDE the
# repo tree, so Claude/Codex/Grok run there record an external cwd shaped like
# <root>/<repo>/<slug>[/subdir]. normalize_cwd() maps those back to the real repo,
# so worktree-based agent work is attributed to the repo it belongs to. Extend via
# config.json {"worktree_roots": [...], "oneshot_roots": [...]}.
WORKTREE_ROOTS_DEFAULT = [
    os.path.join(HOME, ".superconductor", "worktrees"),   # Superconductor
    os.path.join(HOME, "conductor", "workspaces"),        # Conductor.app
]
# Throwaway runs that aren't a repo checkout; attributed to the dev root.
ONESHOT_ROOTS_DEFAULT = [
    os.path.join(HOME, ".superconductor", "one-shot"),    # /<name>/... (no repo)
]
# Mutable copies; resolve_unit() may override them from config.json.
WORKTREE_ROOTS = list(WORKTREE_ROOTS_DEFAULT)
ONESHOT_ROOTS = list(ONESHOT_ROOTS_DEFAULT)
# Claude Cowork (local agent mode) persists each VM's Claude Code transcript to
# the host under these roots, in the standard transcript format.
COWORK_ROOTS = (
    os.path.join(HOME, "Library", "Application Support", "Claude", "local-agent-mode-sessions"),
    os.path.join(HOME, "Library", "Application Support", "Claude", "claude-code-sessions"),
)
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(CLAUDE_DIR, "eod-review")

# Where real repos live, so an orchestrator worktree <repo> can be resolved to a
# real checkout AND so an aggregate can auto-discover repos (incl. brand-new ones).
# Default: whichever common code folders exist. Set it explicitly in config.json
# {"dev_roots": [...], "personal": [...]}.
_DEV_ROOT_CANDIDATES = ("development", "dev", "code", "projects", "src", "repos",
                        "Developer", "workspace")
DEV_ROOTS_DEFAULT = ([p for p in (os.path.join(HOME, n) for n in _DEV_ROOT_CANDIDATES)
                      if os.path.isdir(p)]
                     or [os.path.join(HOME, "development")])
# Personal projects (repo names): kept OUT of work totals and shown as a separate
# line, but still fully reported when explicitly targeted (--unit / --path).
# None by default; list them in config.json's "personal".
PERSONAL_DEFAULT: list = []

# USD per 1M tokens. Estimate only; override via pricing.json. Anthropic standard
# ratios: cache-write-5m = 1.25x input, cache-write-1h = 2x input, read = 0.1x.
DEFAULT_PRICING = {
    "opus": {"input": 15.0, "output": 75.0, "cw5m": 18.75, "cw1h": 30.0, "read": 1.5},
    "sonnet": {"input": 3.0, "output": 15.0, "cw5m": 3.75, "cw1h": 6.0, "read": 0.3},
    "haiku": {"input": 1.0, "output": 5.0, "cw5m": 1.25, "cw1h": 2.0, "read": 0.1},
    # fable-5 pricing is a placeholder (opus-tier) until confirmed — edit pricing.json.
    "fable": {"input": 15.0, "output": 75.0, "cw5m": 18.75, "cw1h": 30.0, "read": 1.5},
    # gpt-5 family (Codex CLI). OpenAI bills no separate cache-write tier, so cw*
    # are never populated for codex usage. PLACEHOLDER list-price estimate — edit
    # pricing.json once confirmed for gpt-5.4 / gpt-5.5.
    "gpt": {"input": 1.25, "output": 10.0, "cw5m": 1.25, "cw1h": 1.25, "read": 0.125},
    # grok-4.5 (Grok CLI, xAI). No separate cache-write tier; cached prompt tokens
    # bill at the discounted read rate. PLACEHOLDER list-price estimate — edit
    # pricing.json once confirmed for grok-4.5.
    "grok": {"input": 3.0, "output": 15.0, "cw5m": 3.0, "cw1h": 3.0, "read": 0.75},
    # Gemini (Gemini CLI, or any agent running a Gemini model). PLACEHOLDER
    # list-price estimate — edit pricing.json.
    "gemini": {"input": 2.0, "output": 12.0, "cw5m": 2.0, "cw1h": 2.0, "read": 0.2},
    "unknown": {"input": 15.0, "output": 75.0, "cw5m": 18.75, "cw1h": 30.0, "read": 1.5},
}


# ----------------------------- resolution ---------------------------------- #


def run_git(path: str, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", path, *args],
            capture_output=True, text=True, check=False,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def load_json(path: str) -> dict:
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return {}


def load_pricing(override: str | None) -> dict:
    pricing = {k: dict(v) for k, v in DEFAULT_PRICING.items()}
    candidates = [
        override,
        os.path.join(CONFIG_DIR, "pricing.json"),
        os.path.join(SKILL_DIR, "pricing.json"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            for model, rates in load_json(c).items():
                pricing[model] = {**pricing.get(model, {}), **rates}
            break
    return pricing


def load_units() -> dict:
    for c in (os.path.join(CONFIG_DIR, "units.json"),
              os.path.join(SKILL_DIR, "units.json")):
        if os.path.isfile(c):
            return load_json(c)
    return {}


def load_config() -> dict:
    """Optional ~/.claude/eod-review/config.json: {dev_roots:[...], personal:[...]}."""
    for c in (os.path.join(CONFIG_DIR, "config.json"),
              os.path.join(SKILL_DIR, "config.json")):
        if os.path.isfile(c):
            return load_json(c)
    return {}


_REPO_DIR_CACHE: dict = {}


def resolve_repo_dir(repo: str, dev_roots: list) -> str | None:
    """Real checkout path for a worktree's <repo> name, cached.

    Prefers ``<dev_root>/<repo>`` (the usual case); if the repo lives nested
    under a dev root (e.g. clients/acme/api) it is found by a
    bounded search, preferring a .git-bearing dir. Falls back to
    ``<dev_root>/<repo>`` so worktree usage still groups by repo name even when
    the checkout can't be located.
    """
    key = (repo, tuple(dev_roots))
    if key in _REPO_DIR_CACHE:
        return _REPO_DIR_CACHE[key]
    result = None
    for root in dev_roots:
        cand = os.path.join(root, repo)
        if os.path.isdir(cand):
            result = cand
            break
    if result is None:
        for root in dev_roots:
            for depth in (1, 2, 3):
                hits = [h for h in glob.glob(os.path.join(root, *(["*"] * depth), repo))
                        if os.path.isdir(h)]
                git_hits = [h for h in hits if os.path.exists(os.path.join(h, ".git"))]
                pick = git_hits or hits
                if pick:
                    result = sorted(pick)[0]
                    break
            if result:
                break
    if result is None and dev_roots:
        result = os.path.join(dev_roots[0], repo)
    _REPO_DIR_CACHE[key] = result
    return result


def normalize_cwd(cwd: str | None, dev_roots: list) -> str | None:
    """Map a recorded cwd to the real repo path it belongs to.

    Claude/Codex/Grok launched by an orchestrator (Superconductor, Conductor)
    run in worktrees checked out *outside* the repo tree
    (``<worktree_root>/<repo>/<slug>/…``), so their logged cwd would otherwise
    never match a repo scan. We collapse such a cwd to the real ``<repo>``
    checkout. ``one-shot`` runs aren't tied to a repo, so they attribute to the
    first dev root — counted in a dev-wide aggregate, owned by no single repo.
    In-repo worktrees (``<repo>/.worktrees/…``) already sit under the repo, so
    prefix matching catches them without remapping. Everything else is unchanged.
    """
    if not cwd:
        return cwd
    p = cwd.rstrip("/")
    for base in ONESHOT_ROOTS:
        if p == base or p.startswith(base + "/"):
            return dev_roots[0] if dev_roots else p
    for base in WORKTREE_ROOTS:
        if p.startswith(base + "/"):
            repo = p[len(base) + 1:].split("/", 1)[0]
            if repo:
                return resolve_repo_dir(repo, dev_roots) or p
    return p


def is_personal(norm_cwd: str | None, personal: list, dev_roots: list) -> bool:
    """True if a (normalized) cwd belongs to a personal project."""
    if not norm_cwd:
        return False
    p = norm_cwd.rstrip("/")
    for name in personal:
        for root in dev_roots:
            repo = os.path.join(root, name).rstrip("/")
            if p == repo or p.startswith(repo + "/"):
                return True
        # Fallback for sources that record the real path directly (Grok/Codex):
        if p.endswith("/" + name) or ("/" + name + "/") in p:
            return True
    return False


def local_date_bounds(since: str | None, until: str | None, days: int | None):
    today = dt.date.today()
    if days is not None:
        start = today - dt.timedelta(days=max(0, days - 1))
        end = today
    else:
        start = dt.date.fromisoformat(since) if since else today
        end = dt.date.fromisoformat(until) if until else today
    return start, end


def resolve_unit(args) -> dict:
    """Returns {path, branch, author, all_branches, all_authors, dev_roots,
    personal, unit_is_personal}."""
    unit = {}
    if args.unit:
        units = load_units()
        if args.unit not in units:
            sys.exit(f"Unknown unit '{args.unit}'. Defined: {', '.join(units) or '(none)'}")
        unit = units[args.unit]

    path = os.path.abspath(os.path.expanduser(
        args.path or unit.get("path") or os.getcwd()))

    all_branches = args.all_branches or unit.get("all_branches", False)
    branch = None
    if not all_branches:
        branch = args.branch or unit.get("branch") or run_git(path, "rev-parse", "--abbrev-ref", "HEAD") or None

    all_authors = args.all_authors or unit.get("all_authors", False)
    author = None
    if not all_authors:
        author = args.author or unit.get("author") or run_git(path, "config", "user.email") or None

    cfg = load_config()
    dev_roots = [os.path.abspath(os.path.expanduser(r))
                 for r in (cfg.get("dev_roots") or DEV_ROOTS_DEFAULT)]
    personal = cfg.get("personal") or PERSONAL_DEFAULT
    # Optional named groups of repos, e.g. {"consulting": ["acme-site"], "side": ["blog"]}.
    # Each group gets its own section in the report; repos in no group are "work".
    groups = {str(name): list(repos) for name, repos in (cfg.get("groups") or {}).items()
              if isinstance(repos, list) and repos}
    # Let config extend the orchestrator worktree roots (Superconductor/Conductor).
    global WORKTREE_ROOTS, ONESHOT_ROOTS
    if cfg.get("worktree_roots"):
        WORKTREE_ROOTS = [os.path.abspath(os.path.expanduser(r)) for r in cfg["worktree_roots"]]
    if cfg.get("oneshot_roots"):
        ONESHOT_ROOTS = [os.path.abspath(os.path.expanduser(r)) for r in cfg["oneshot_roots"]]
    # When the unit itself targets a personal project, report it in full (do not
    # split it out) — the exclusion only applies to broader work reviews.
    unit_is_personal = is_personal(normalize_cwd(path, dev_roots), personal, dev_roots)

    return {"path": path, "branch": branch, "author": author,
            "all_branches": all_branches, "all_authors": all_authors,
            "dev_roots": dev_roots, "personal": personal, "groups": groups,
            "unit_is_personal": unit_is_personal}


# ------------------------------- commits ----------------------------------- #


def is_git_repo(path: str) -> bool:
    return os.path.exists(os.path.join(path, ".git"))


def discover_repos(root: str, max_depth: int = 3) -> list[str]:
    """Top-level git repos at/under ``root`` (self if it is one).

    Descends at most ``max_depth`` levels, stops at the first .git it finds on a
    branch (so nested worktrees under a repo aren't double-counted), and skips
    heavy/irrelevant dirs. Superconductor worktrees are intentionally excluded —
    their commits already reach the real repo via ``git log --all``.
    """
    if is_git_repo(root):
        return [root]
    skip = {"node_modules", ".git", "dist", "build", ".next", ".venv",
            "venv", "__pycache__", ".superconductor", ".conductor", ".worktrees"}
    repos: list[str] = []
    root = root.rstrip("/")
    base_depth = root.count(os.sep)
    for cur, dirs, _files in os.walk(root):
        if cur.count(os.sep) - base_depth >= max_depth:
            dirs[:] = []
            continue
        if is_git_repo(cur) and cur != root:
            repos.append(cur)
            dirs[:] = []  # don't descend into a repo
            continue
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
    return sorted(repos)


def _log_repo(repo: str, unit: dict, start: dt.date, end: dt.date) -> list[dict]:
    fmt = "%h%x1f%ad%x1f%an%x1f%s"
    rev_args = ["--all"] if unit["all_branches"] else \
        [unit["branch"] if unit["branch"] else "HEAD"]
    cmd = [
        "log", *rev_args,
        f"--since={start.isoformat()} 00:00:00",
        f"--until={end.isoformat()} 23:59:59",
        f"--pretty=format:{fmt}", "--date=format:%Y-%m-%d %H:%M",
    ]
    if unit["author"]:
        cmd.append(f"--author={unit['author']}")
    tag = os.path.basename(repo.rstrip("/"))
    commits = []
    for line in run_git(repo, *cmd).splitlines():
        if not line.strip():
            continue
        h, d, a, s = (line.split("\x1f") + ["", "", "", ""])[:4]
        commits.append({"hash": h, "date": d, "author": a, "subject": s, "repo": tag})
    return commits


def dedupe_commits(commits: list[dict]) -> list[dict]:
    """Drop commits seen more than once (same SHA + subject), keeping the first.

    Sibling worktrees/clones of one repo share object history, so ``git log
    --all`` in each surfaces the same commit; a SHA is globally unique, so this
    collapses those duplicates without merging genuinely distinct commits.
    """
    seen: set = set()
    out: list[dict] = []
    for c in commits:
        key = (c.get("hash"), c.get("subject"))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def collect_commits(unit: dict, start: dt.date, end: dt.date) -> tuple[list, list]:
    """(work_commits, personal_commits) across the unit's repo(s).

    A bare container path (e.g. ~/development) fans out to every child git repo
    so brand-new repos are picked up automatically; a repo path logs just itself.
    Duplicate SHAs from sibling worktrees/clones are collapsed.
    """
    repos = discover_repos(unit["path"])
    work: list[dict] = []
    personal: list[dict] = []
    for repo in repos:
        commits = _log_repo(repo, unit, start, end)
        if (not unit["unit_is_personal"]
                and is_personal(normalize_cwd(repo, unit["dev_roots"]),
                                unit["personal"], unit["dev_roots"])):
            personal.extend(commits)
        else:
            if unit.get("groups"):
                group = group_of(normalize_cwd(repo, unit["dev_roots"]), unit) or "work"
                commits = [{**c, "group": group} for c in commits]
            work.extend(commits)
    return dedupe_commits(work), dedupe_commits(personal)


# -------------------------------- tokens ----------------------------------- #


def model_bucket(model: str | None) -> str:
    m = (model or "").lower()
    if "synthetic" in m or not m:
        return "synthetic"
    for key in ("opus", "sonnet", "haiku", "fable", "gpt", "grok", "gemini"):
        if key in m:
            return key
    return "unknown"


def parse_local_date(ts: str | None):
    if not ts:
        return None
    try:
        d = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return d.astimezone().date()
    except Exception:
        return None


def path_matches(cwd: str | None, target: str) -> bool:
    if not cwd:
        return False
    target = target.rstrip("/")
    return cwd == target or cwd.startswith(target + "/")


def empty_bucket() -> dict:
    return {"input": 0, "cw5m": 0, "cw1h": 0, "cw_other": 0, "read": 0, "output": 0, "calls": 0}


def add_usage(by_model: dict, bucket: str, usage: dict) -> None:
    """Accumulate one Claude `usage` object into by_model[bucket] (in place).

    Shared by every collector that reads the standard Claude transcript format
    (Claude Code transcripts and Cowork's persisted VM transcripts) so the token
    arithmetic lives in exactly one place.
    """
    b = by_model.setdefault(bucket, empty_bucket())
    cc = usage.get("cache_creation") or {}
    cw5m = cc.get("ephemeral_5m_input_tokens", 0)
    cw1h = cc.get("ephemeral_1h_input_tokens", 0)
    cc_total = usage.get("cache_creation_input_tokens", 0)
    b["input"] += usage.get("input_tokens", 0)
    b["cw5m"] += cw5m
    b["cw1h"] += cw1h
    b["cw_other"] += max(0, cc_total - cw5m - cw1h)
    b["read"] += usage.get("cache_read_input_tokens", 0)
    b["output"] += usage.get("output_tokens", 0)
    b["calls"] += 1


# Token buckets for config.json "groups", filled by sink_for() across every
# collector: {group name: by_model dict}. Empty when no groups are configured.
GROUP_SINKS: dict = {}


def group_of(ncwd: str | None, unit: dict) -> str | None:
    """The configured group a (normalized) cwd belongs to, or None."""
    for name, repos in (unit.get("groups") or {}).items():
        if is_personal(ncwd, repos, unit["dev_roots"]):  # same repo-name matcher
            return name
    return None


def sink_for(work: dict, personal: dict, ncwd: str | None, unit: dict) -> dict:
    """Pick the by_model dict for a (normalized) cwd: personal, a named group, or work."""
    if (not unit["unit_is_personal"]
            and is_personal(ncwd, unit["personal"], unit["dev_roots"])):
        return personal
    group = group_of(ncwd, unit)
    if group:
        return GROUP_SINKS.setdefault(group, {})
    return work


def collect_tokens(unit: dict, start: dt.date, end: dt.date) -> tuple[dict, dict]:
    work: dict[str, dict] = {}
    personal: dict[str, dict] = {}
    files = glob.glob(os.path.join(PROJECTS_DIR, "**", "*.jsonl"), recursive=True)
    for f in files:
        try:
            fh = open(f)
        except Exception:
            continue
        with fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                msg = o.get("message")
                if not isinstance(msg, dict):
                    continue
                usage = msg.get("usage")
                if not usage:
                    continue
                d = parse_local_date(o.get("timestamp"))
                if d is None or d < start or d > end:
                    continue
                ncwd = normalize_cwd(o.get("cwd"), unit["dev_roots"])
                if not path_matches(ncwd, unit["path"]):
                    continue
                if unit["branch"] and o.get("gitBranch") != unit["branch"]:
                    continue

                sink = sink_for(work, personal, ncwd, unit)
                add_usage(sink, model_bucket(msg.get("model")), usage)
    return work, personal


def collect_codex_tokens(unit: dict, start: dt.date, end: dt.date) -> dict:
    """Codex CLI rollouts -> same by_model shape as collect_tokens (folded in).

    Codex writes JSONL rollouts under ~/.codex/{sessions,archived_sessions}.
    Unlike Claude transcripts, cwd is recorded once per session/turn (not per
    line) and token usage arrives as per-turn deltas in an `event_msg` whose
    payload.type == "token_count" (info.last_token_usage). Summed deltas equal
    the session's cumulative total.

    Caveats baked into the attribution:
    - No git branch is recorded, so codex usage matches by **worktree (cwd) +
      day only**; unit["branch"] is intentionally ignored for this slice. For a
      worktree that is a dedicated branch checkout (the usual case) path and
      branch coincide anyway.
    - OpenAI has no cache-write tier, so cw5m/cw1h stay 0; cached_input_tokens
      maps to `read`, and fresh input is input_tokens - cached_input_tokens.
    - Superconductor runs Codex in an external worktree, so the recorded cwd is
      remapped to the real repo via normalize_cwd() before matching.
    """
    work: dict[str, dict] = {}
    personal: dict[str, dict] = {}
    roots = (os.path.join(CODEX_DIR, "sessions"),
             os.path.join(CODEX_DIR, "archived_sessions"))
    files: list[str] = []
    for root in roots:
        files.extend(glob.glob(os.path.join(root, "**", "rollout-*.jsonl"), recursive=True))

    for f in files:
        try:
            fh = open(f)
        except Exception:
            continue
        cwd: str | None = None
        with fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                payload = o.get("payload")
                if not isinstance(payload, dict):
                    continue
                kind = o.get("type")
                if kind in ("session_meta", "turn_context"):
                    cwd = payload.get("cwd") or cwd
                    continue
                if kind != "event_msg" or payload.get("type") != "token_count":
                    continue
                d = parse_local_date(o.get("timestamp"))
                if d is None or d < start or d > end:
                    continue
                ncwd = normalize_cwd(cwd, unit["dev_roots"])
                if not path_matches(ncwd, unit["path"]):
                    continue

                last = (payload.get("info") or {}).get("last_token_usage") or {}
                inp = last.get("input_tokens", 0)
                cached = last.get("cached_input_tokens", 0)
                b = sink_for(work, personal, ncwd, unit).setdefault("gpt", empty_bucket())
                b["input"] += max(0, inp - cached)
                b["read"] += cached
                b["output"] += last.get("output_tokens", 0)
                b["calls"] += 1
    return work, personal


def grok_session_index() -> dict:
    """session_id -> (cwd, branch, model) from every Grok summary.json."""
    idx: dict[str, tuple] = {}
    for sm in glob.glob(os.path.join(GROK_SESSIONS_DIR, "*", "*", "summary.json")):
        o = load_json(sm)
        info = o.get("info") or {}
        sid = info.get("id") or os.path.basename(os.path.dirname(sm))
        if sid:
            idx[sid] = (info.get("cwd"), o.get("head_branch"), o.get("current_model_id"))
    return idx


def collect_grok_tokens(unit: dict, start: dt.date, end: dt.date) -> tuple[dict, dict]:
    """Grok CLI usage -> (work, personal) by_model splits (folded in by default).

    Grok writes per-turn token usage to one rolling log
    (~/.grok/logs/unified.jsonl) on ``shell.turn.inference_done`` lines, keyed by
    session id (``sid``); the session's cwd/branch/model come from its
    summary.json. Attribution is by worktree (cwd, normalized for superconductor)
    + day; branch is recorded per session (not per turn), so — like Codex — the
    branch filter is not applied. No cache-write tier: cached_prompt_tokens ->
    read, fresh = prompt - cached, output = completion_tokens (reasoning_tokens
    is a subset of completion, not counted again).

    Caveat: the log is not date-partitioned and only spans back to when grok-cli
    logging began, so weeks before that under-report Grok.
    """
    work: dict[str, dict] = {}
    personal: dict[str, dict] = {}
    if not os.path.isfile(GROK_LOG):
        return work, personal
    idx = grok_session_index()
    try:
        fh = open(GROK_LOG)
    except Exception:
        return work, personal
    with fh:
        for line in fh:
            if '"shell.turn.inference_done"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            d = parse_local_date(o.get("ts"))
            if d is None or d < start or d > end:
                continue
            cwd, _branch, model = idx.get(o.get("sid"), (None, None, None))
            ncwd = normalize_cwd(cwd, unit["dev_roots"])
            if not path_matches(ncwd, unit["path"]):
                continue
            ctx = o.get("ctx") or {}
            prompt = ctx.get("prompt_tokens", 0)
            cached = ctx.get("cached_prompt_tokens", 0)
            b = sink_for(work, personal, ncwd, unit).setdefault(
                model_bucket(model or "grok"), empty_bucket())
            b["input"] += max(0, prompt - cached)
            b["read"] += cached
            b["output"] += ctx.get("completion_tokens", 0)
            b["calls"] += 1
    return work, personal


def merge_by_model(a: dict, b: dict) -> dict:
    """Immutably combine two by_model dicts into a fresh one (no mutation)."""
    out = {name: dict(bucket) for name, bucket in a.items()}
    for name, bucket in b.items():
        base = out.get(name, empty_bucket())
        out[name] = {k: base.get(k, 0) + bucket.get(k, 0)
                     for k in set(base) | set(bucket)}
    return out


def merge_split(a: tuple, b: tuple) -> tuple:
    """Combine two (work, personal) by_model splits into one fresh split."""
    return (merge_by_model(a[0], b[0]), merge_by_model(a[1], b[1]))


def cowork_session_folders(transcript_path: str, cache: dict) -> list:
    """Map a Cowork transcript to its session's userSelectedFolders (host repos).

    Transcript lives at .../local_<id>/.claude/projects/<slug>/<file>.jsonl; the
    session metadata is the sibling file '<.../local_<id>>.json'. Cached per
    session dir so the metadata is read once even when a session has many
    transcripts (main + subagents).
    """
    parts = transcript_path.split(os.sep)
    sess_dir = None
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].startswith("local_"):
            sess_dir = os.sep.join(parts[: i + 1])
            break
    if not sess_dir:
        return []
    if sess_dir in cache:
        return cache[sess_dir]
    meta_path = sess_dir + ".json"
    folders = load_json(meta_path).get("userSelectedFolders") or [] if os.path.isfile(meta_path) else []
    cache[sess_dir] = folders
    return folders


def folders_match(folders: list, target: str) -> bool:
    """True if any selected folder is the target, under it, or contains it."""
    target = target.rstrip("/")
    for f in folders:
        f = (f or "").rstrip("/")
        if f and (path_matches(f, target) or path_matches(target, f)):
            return True
    return False


def collect_cowork_tokens(unit: dict, start: dt.date, end: dt.date) -> dict:
    """Claude Cowork (local agent mode) usage, folded into the same by_model shape.

    Cowork runs Claude Code in a VM and persists that VM's transcript to the host
    in the *standard* transcript format, so usage parses exactly like Claude Code.
    The transcript cwd/gitBranch are VM-internal, so attribution comes from the
    session metadata's `userSelectedFolders` (the host repos mounted into the
    session): a session is counted in full for any unit whose path it touches.
    A session spanning several repos cannot be split per-repo, so its tokens
    attribute as a whole — exact at the dev-wide aggregate, possibly overlapping
    only if you separately sum narrow per-repo units.
    """
    work: dict[str, dict] = {}
    personal: dict[str, dict] = {}
    folder_cache: dict[str, list] = {}
    files: list[str] = []
    for root in COWORK_ROOTS:
        files.extend(glob.glob(
            os.path.join(root, "**", ".claude", "projects", "**", "*.jsonl"),
            recursive=True))

    for f in files:
        folders = cowork_session_folders(f, folder_cache)
        if not folders_match(folders, unit["path"]):
            continue
        # A session counts as personal only if every mounted folder is personal.
        sink = personal if (
            not unit["unit_is_personal"] and folders
            and all(is_personal(normalize_cwd(ff, unit["dev_roots"]),
                                unit["personal"], unit["dev_roots"])
                    for ff in folders if ff)
        ) else work
        try:
            fh = open(f)
        except Exception:
            continue
        with fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                msg = o.get("message")
                if not isinstance(msg, dict):
                    continue
                usage = msg.get("usage")
                if not usage:
                    continue
                d = parse_local_date(o.get("timestamp"))
                if d is None or d < start or d > end:
                    continue
                add_usage(sink, model_bucket(msg.get("model")), usage)
    return work, personal


# ----------------------------- other agents -------------------------------- #


def _ms_date(ms):
    """Local date for an epoch-milliseconds value, or None."""
    try:
        return dt.datetime.fromtimestamp(int(ms) / 1000).date()
    except Exception:
        return None


def _ro_db(path: str):
    """Read-only SQLite connection, or None. Never writes to an agent's database."""
    if not os.path.isfile(path):
        return None
    try:
        return sqlite3.connect("file:" + path + "?mode=ro", uri=True, timeout=2)
    except Exception:
        return None


def _file_uri_path(uri) -> str | None:
    if isinstance(uri, str) and uri.startswith("file://"):
        return uri[len("file://"):]
    return None


def gemini_project_dirs(dev_roots: list) -> dict:
    """Map each ~/.gemini/tmp/<dir> name to the project path it belongs to.

    Gemini CLI names the folder after the project (projects.json: path -> name)
    or, in older versions, after sha256(path). Old hashed folders are not in
    projects.json, so the home folder, the dev roots and every repo under them
    are hashed as candidates too.
    """
    out: dict = {}
    projects = (load_json(os.path.join(GEMINI_DIR, "projects.json")) or {}).get("projects") or {}
    for path, name in projects.items():
        out[name] = path
    candidates = [HOME, *projects]
    for root in dev_roots:
        candidates.append(root)
        candidates.extend(discover_repos(root))
    for path in candidates:
        out.setdefault(hashlib.sha256(path.encode()).hexdigest(), path)
    return out


def collect_gemini_tokens(unit: dict, start: dt.date, end: dt.date) -> tuple[dict, dict]:
    """Gemini CLI usage -> (work, personal). Each model reply in
    ~/.gemini/tmp/<project>/chats/*.json carries a timestamp, model and tokens.
    `cached` is a subset of `input`; `thoughts` bills as output. Sessions whose
    folder cannot be mapped to a project path are skipped."""
    work: dict[str, dict] = {}
    personal: dict[str, dict] = {}
    dirs = gemini_project_dirs(unit["dev_roots"])
    for f in glob.glob(os.path.join(GEMINI_DIR, "tmp", "*", "chats", "*.json")):
        cwd = dirs.get(os.path.basename(os.path.dirname(os.path.dirname(f))))
        ncwd = normalize_cwd(cwd, unit["dev_roots"])
        if not path_matches(ncwd, unit["path"]):
            continue
        for m in (load_json(f) or {}).get("messages") or []:
            t = m.get("tokens")
            if m.get("type") != "gemini" or not isinstance(t, dict):
                continue
            d = parse_local_date(m.get("timestamp"))
            if d is None or d < start or d > end:
                continue
            cached = t.get("cached", 0)
            b = sink_for(work, personal, ncwd, unit).setdefault(
                model_bucket(m.get("model") or "gemini"), empty_bucket())
            b["input"] += max(0, t.get("input", 0) - cached)
            b["read"] += cached
            b["output"] += t.get("output", 0) + t.get("thoughts", 0)
            b["calls"] += 1
    return work, personal


def collect_opencode_tokens(unit: dict, start: dt.date, end: dt.date) -> tuple[dict, dict]:
    """opencode usage -> (work, personal), from its SQLite store. Each assistant
    message records the model, the folder it ran in and its tokens."""
    work: dict[str, dict] = {}
    personal: dict[str, dict] = {}
    db = _ro_db(OPENCODE_DB)
    if db is None:
        return work, personal
    try:
        rows = db.execute("select data from message").fetchall()
    except Exception:
        return work, personal
    finally:
        db.close()
    for (data,) in rows:
        try:
            o = json.loads(data)
        except Exception:
            continue
        t = o.get("tokens")
        if o.get("role") != "assistant" or not isinstance(t, dict):
            continue
        d = _ms_date((o.get("time") or {}).get("created"))
        if d is None or d < start or d > end:
            continue
        ncwd = normalize_cwd((o.get("path") or {}).get("cwd"), unit["dev_roots"])
        if not path_matches(ncwd, unit["path"]):
            continue
        cache = t.get("cache") or {}
        b = sink_for(work, personal, ncwd, unit).setdefault(
            model_bucket(o.get("modelID") or "unknown"), empty_bucket())
        b["input"] += t.get("input", 0)
        b["cw5m"] += cache.get("write", 0)
        b["read"] += cache.get("read", 0)
        b["output"] += t.get("output", 0) + t.get("reasoning", 0)
        b["calls"] += 1
    return work, personal


def count_cursor_sessions(unit: dict, start: dt.date, end: dt.date) -> dict:
    """Cursor agent sessions active in the window. Cursor keeps no token counts
    on disk, so sessions are all that can be reported."""
    db = _ro_db(CURSOR_DB) or _ro_db(CURSOR_DB_LINUX)
    if db is None:
        return {}
    try:
        rows = db.execute("select createdAt, lastUpdatedAt, value from composerHeaders").fetchall()
    except Exception:
        return {}
    finally:
        db.close()
    n = 0
    for created, updated, value in rows:
        first, last = _ms_date(created), _ms_date(updated or created)
        if first is None or last is None or last < start or first > end:
            continue
        try:
            uri = ((json.loads(value or "{}").get("workspaceIdentifier") or {}).get("uri") or {})
        except Exception:
            continue
        ncwd = normalize_cwd(uri.get("fsPath") or uri.get("path"), unit["dev_roots"])
        if path_matches(ncwd, unit["path"]):
            n += 1
    return {"sessions": n} if n else {}


def count_antigravity_sessions(unit: dict, start: dt.date, end: dt.date) -> dict:
    """Antigravity conversations last touched in the window. Its transcripts are
    not readable, so only the summary index (folders, step count) is used."""
    db = _ro_db(ANTIGRAVITY_DB)
    if db is None:
        return {}
    try:
        rows = db.execute(
            "select step_count, last_modified_time, workspace_uris from conversation_summaries"
        ).fetchall()
    except Exception:
        return {}
    finally:
        db.close()
    sessions = steps = 0
    for step_count, modified, uris in rows:
        d = parse_local_date((modified or "").replace(" ", "T", 1))
        if d is None or d < start or d > end:
            continue
        try:
            paths = [_file_uri_path(u) for u in json.loads(uris or "[]")]
        except Exception:
            continue
        if any(path_matches(normalize_cwd(p, unit["dev_roots"]), unit["path"]) for p in paths if p):
            sessions += 1
            steps += step_count or 0
    return {"sessions": sessions, "steps": steps} if sessions else {}


def parse_skip(value: str | None) -> set:
    return {v.strip().lower() for v in (value or "").split(",") if v.strip()}


def collect_other_agents(unit: dict, start: dt.date, end: dt.date, skip: set) -> tuple:
    """Everything beyond Claude Code, Codex, Grok and Cowork.

    Returns ((work, personal) token split, sessions, included) where `sessions`
    holds agents that keep no token counts ({"cursor": {"sessions": 3}}) and
    `included` lists the agents that were read.
    """
    split: tuple = ({}, {})
    sessions: dict = {}
    included = [a for a in OTHER_AGENTS if a not in skip]
    if "gemini" in included:
        split = merge_split(split, collect_gemini_tokens(unit, start, end))
    if "opencode" in included:
        split = merge_split(split, collect_opencode_tokens(unit, start, end))
    if "cursor" in included:
        found = count_cursor_sessions(unit, start, end)
        if found:
            sessions["cursor"] = found
    if "antigravity" in included:
        found = count_antigravity_sessions(unit, start, end)
        if found:
            sessions["antigravity"] = found
    return split, sessions, included



def cost_of(bucket_name: str, b: dict, pricing: dict) -> float:
    if bucket_name == "synthetic":
        return 0.0
    r = pricing.get(bucket_name, pricing["unknown"])
    return (
        b["input"] * r["input"]
        + (b["cw5m"]) * r["cw5m"]
        + (b["cw1h"]) * r["cw1h"]
        + (b["cw_other"]) * r["cw5m"]
        + b["read"] * r["read"]
        + b["output"] * r["output"]
    ) / 1_000_000.0


def summarize_tokens(by_model: dict, pricing: dict) -> dict:
    totals = empty_bucket()
    models = {}
    total_cost = 0.0
    for name, b in by_model.items():
        for k in totals:
            totals[k] += b[k]
        c = cost_of(name, b, pricing)
        total_cost += c
        models[name] = {**b, "cost_usd": round(c, 2)}
    fresh_input = totals["input"] + totals["cw5m"] + totals["cw1h"] + totals["cw_other"]
    cache_read = totals["read"]
    grand = fresh_input + cache_read + totals["output"]
    return {
        "by_model": models,
        "totals": {
            "calls": totals["calls"],
            "fresh_input": fresh_input,
            "cache_read": cache_read,
            "output": totals["output"],
            "grand_total": grand,
        },
        "cost_usd_estimate": round(total_cost, 2),
    }


def summarize_groups(unit: dict, work_bm: dict, commits: list, pricing: dict) -> tuple:
    """(headline tokens, by_group). Headline = ungrouped work + every named group.

    by_group is None unless config.json names groups; otherwise it maps "work"
    (repos in no group) and each group to its commit count and token summary.
    Cowork sessions are not split by group and stay under "work".
    """
    if not unit.get("groups"):
        return summarize_tokens(work_bm, pricing), None
    total = work_bm
    by_group = {"work": {"commits": 0, "tokens": summarize_tokens(work_bm, pricing)}}
    for name in unit["groups"]:
        bm = GROUP_SINKS.get(name, {})
        total = merge_by_model(total, bm)
        by_group[name] = {"commits": 0, "tokens": summarize_tokens(bm, pricing)}
    for c in commits:
        by_group.setdefault(c.get("group", "work"), {"commits": 0, "tokens": summarize_tokens({}, pricing)})
        by_group[c.get("group", "work")]["commits"] += 1
    return summarize_tokens(total, pricing), by_group


# ------------------------------- rendering --------------------------------- #


def human(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n/1e9:.2f}B"
    if n >= 1_000_000:
        return f"{n/1e6:.2f}M"
    if n >= 1_000:
        return f"{n/1e3:.1f}K"
    return str(n)


def sources_note(report: dict) -> str:
    extra = (["Codex"] if report.get("includes_codex") else []) \
        + (["Grok"] if report.get("includes_grok") else []) \
        + (["Cowork"] if report.get("includes_cowork") else []) \
        + [a.capitalize() for a in report.get("includes_other") or []
           if a in ("gemini", "opencode")]
    # Worktree normalization always runs (incl. for Claude Code), so orchestrator
    # worktree usage is folded into every report regardless of the Codex/Grok flags.
    return ("incl. subagents + workflows" + "".join(" + " + e for e in extra)
            + " (incl. Superconductor/Conductor worktrees)")


def render_commit(c: dict) -> str:
    repo = f"[{c['repo']}] " if c.get("repo") else ""
    if c.get("group"):
        repo = f"({c['group']}) {repo}"
    return f"  {c['date']}  {c['hash']}  {repo}{c['subject']}"


def render_token_block(lines: list, tk: dict, header: str, note: str) -> None:
    t = tk["totals"]
    lines.append(f"\n{header} ({human(t['calls'])} model turns {note})")
    lines.append(f"  output (generated): {human(t['output'])}")
    lines.append(f"  fresh input:        {human(t['fresh_input'])}")
    lines.append(f"  cache reads:        {human(t['cache_read'])}  (~10% rate)")
    lines.append(f"  grand total:        {human(t['grand_total'])}")
    lines.append("\n  per model:")
    for name, b in sorted(tk["by_model"].items(), key=lambda kv: -kv[1]["output"]):
        fi = b["input"] + b["cw5m"] + b["cw1h"] + b["cw_other"]
        lines.append(
            f"    {name:10} out={human(b['output']):>8}  "
            f"in={human(fi):>8}  read={human(b['read']):>8}  ${b['cost_usd']:.2f}"
        )
    lines.append(f"\n  est. cost: ${tk['cost_usd_estimate']:.2f}  "
                 "(ESTIMATE from editable pricing.json — not billed cost)")


def render_groups(lines: list, report: dict) -> None:
    by_group = report.get("by_group")
    if not by_group:
        return
    lines.append("\nBY GROUP")
    for name, g in by_group.items():
        t = g["tokens"]
        lines.append(f"  {name:14} {g['commits']:>4} commits   out={human(t['totals']['output']):>8}"
                     f"   ${t['cost_usd_estimate']:.2f}")


def render_sessions(lines: list, report: dict) -> None:
    sessions = report.get("sessions") or {}
    if not sessions:
        return
    lines.append("\nOTHER AGENTS (these keep no token counts on disk)")
    for name, info in sessions.items():
        steps = f", {info['steps']} steps" if info.get("steps") else ""
        lines.append(f"  {name:12} {info['sessions']} session(s){steps}")


def render_personal(lines: list, report: dict) -> None:
    pc = report.get("personal_commits") or []
    pt = report.get("personal_tokens")
    if not pc and not pt:
        return
    lines.append("\n" + "-" * 64)
    lines.append("PERSONAL PROJECTS — kept separate, NOT in the work totals above")
    lines.append(f"\n  commits ({len(pc)})")
    for c in pc:
        lines.append("  " + render_commit(c).lstrip())
    if pt:
        render_token_block(lines, pt, "  personal tokens", sources_note(report))


def render_text(report: dict) -> str:
    u, w = report["unit"], report["window"]
    lines = []
    lines.append("=" * 64)
    lines.append("EOD REVIEW")
    scope = f"branch={u['branch'] or '(all)'}  author={u['author'] or '(all)'}"
    lines.append(f"  worktree: {u['path']}")
    lines.append(f"  {scope}")
    lines.append(f"  window:   {w['start']} -> {w['end']}")
    lines.append("=" * 64)

    commits = report["commits"]
    lines.append(f"\nCOMMITS ({len(commits)})")
    for c in commits:
        lines.append(render_commit(c))
    if not commits:
        lines.append("  (none in window)")

    render_token_block(lines, report["tokens"], "TOKENS", sources_note(report))
    render_groups(lines, report)
    render_sessions(lines, report)
    render_personal(lines, report)
    lines.append("=" * 64)
    return "\n".join(lines)


# --------------------------------- main ------------------------------------ #


def main() -> None:
    p = argparse.ArgumentParser(description="EOD review: commits + token usage for a work unit.")
    p.add_argument("--unit", help="named work unit from units.json")
    p.add_argument("--path", help="worktree path (default: cwd)")
    p.add_argument("--branch", help="git branch (default: current)")
    p.add_argument("--author", help="commit/author filter email (default: git config user.email)")
    p.add_argument("--since", help="start date YYYY-MM-DD (default: today)")
    p.add_argument("--until", help="end date YYYY-MM-DD (default: today)")
    p.add_argument("--days", type=int, help="last N days inclusive (overrides since/until)")
    p.add_argument("--all-branches", action="store_true", help="do not filter by branch")
    p.add_argument("--all-authors", action="store_true", help="do not filter commits by author")
    p.add_argument("--no-codex", action="store_true",
                   help="exclude Codex CLI token usage (Claude only)")
    p.add_argument("--no-grok", action="store_true",
                   help="exclude Grok CLI token usage")
    p.add_argument("--no-cowork", action="store_true",
                   help="exclude Claude Cowork (local agent mode) token usage")
    p.add_argument("--skip", metavar="AGENTS",
                   help="comma list of other agents to leave out: "
                        "gemini, opencode, cursor, antigravity")
    p.add_argument("--pricing", help="path to a pricing.json override")
    p.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = p.parse_args()

    unit = resolve_unit(args)
    start, end = local_date_bounds(args.since, args.until, args.days)
    pricing = load_pricing(args.pricing)

    commits, personal_commits = collect_commits(unit, start, end)
    split = collect_tokens(unit, start, end)
    includes_codex = not args.no_codex
    includes_grok = not args.no_grok
    includes_cowork = not args.no_cowork
    if includes_codex:
        split = merge_split(split, collect_codex_tokens(unit, start, end))
    if includes_grok:
        split = merge_split(split, collect_grok_tokens(unit, start, end))
    if includes_cowork:
        split = merge_split(split, collect_cowork_tokens(unit, start, end))
    other_split, sessions, includes_other = collect_other_agents(
        unit, start, end, parse_skip(args.skip))
    split = merge_split(split, other_split)
    work_bm, personal_bm = split
    tokens, by_group = summarize_groups(unit, work_bm, commits, pricing)
    personal_tokens = summarize_tokens(personal_bm, pricing) if personal_bm else None

    report = {
        "unit": unit,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "commits": commits,
        "personal_commits": personal_commits,
        "tokens": tokens,
        "personal_tokens": personal_tokens,
        "includes_codex": includes_codex,
        "includes_grok": includes_grok,
        "includes_cowork": includes_cowork,
        "includes_other": includes_other,
        "sessions": sessions,
    }
    if by_group:
        report["by_group"] = by_group

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))


if __name__ == "__main__":
    main()
