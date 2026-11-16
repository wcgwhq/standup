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
import shutil
import re
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

# USD per 1M tokens: Anthropic's API list prices, read on PRICES_AS_OF. Cache
# writes bill at 1.25x input (5 minutes) and 2x input (1 hour); cache reads at
# 0.1x input unless the model lists its own rate. One row per MODEL, because
# prices differ inside a family (Opus 5.5 is $4 in, Opus 5 is $5).
#
# A model with no row here is UNPRICED: its tokens are counted and its cost is
# left out and said so. That covers every non-Anthropic model (Codex, Grok,
# Gemini, opencode's providers) until the user adds a row to pricing.json, e.g.
# {"gpt": {"input": 1.25, "output": 10, "read": 0.125}}. A pricing.json key
# prices every model id that starts with it.
PRICES_AS_OF = "2026-11-03"


def _claude(inp: float, out: float, read: float | None = None) -> dict:
    return {"input": inp, "output": out, "cw5m": inp * 1.25, "cw1h": inp * 2.0,
            "read": inp * 0.1 if read is None else read}


DEFAULT_PRICING = {
    "fable-5-2": _claude(8, 40, 0.20), "mythos-5-2": _claude(8, 40, 0.20),
    "fable-5-1": _claude(10, 50), "mythos-5-1": _claude(10, 50),
    "fable-5": _claude(10, 50), "mythos-5": _claude(10, 50),
    "opus-5-5": _claude(4, 20, 0.20),
    "opus-5": _claude(5, 25), "opus-4-8": _claude(5, 25),
    "opus-4-7": _claude(5, 25), "opus-4-6": _claude(5, 25),
    "sonnet-5-5": _claude(2, 10, 0.10),
    "sonnet-5": _claude(2, 10), "sonnet-4-6": _claude(3, 15),
    "haiku-5-5": _claude(0.10, 0.50), "haiku-4-5": _claude(1, 5),
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
    """Lenient: for other apps' files, where a bad file just means no data."""
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        return {}


def load_user_json(path: str) -> dict:
    """Strict: for the user's own config. A typo must stop the run, because a
    config that silently reads as empty folds personal or client work into the
    work totals."""
    try:
        with open(path) as fh:
            data = json.load(fh)
    except ValueError as exc:
        sys.exit(f"{path} is not valid JSON: {exc}. Fix that line, or move the file away to run without it.")
    except OSError as exc:
        sys.exit(f"Cannot read {path}: {exc}")
    if not isinstance(data, dict):
        sys.exit(f"{path} must hold a JSON object ({{...}}), not a {type(data).__name__}.")
    return data


def load_pricing(override: str | None) -> dict:
    pricing = {k: dict(v) for k, v in DEFAULT_PRICING.items()}
    candidates = [
        override,
        os.path.join(CONFIG_DIR, "pricing.json"),
        os.path.join(SKILL_DIR, "pricing.json"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            for model, rates in load_user_json(c).items():
                if not isinstance(rates, dict) or model.startswith("_"):
                    continue
                merged = {**pricing.get(model, {}), **rates}
                if "input" not in merged or "output" not in merged:
                    sys.exit(f"{c}: \"{model}\" needs at least \"input\" and \"output\" (USD per 1M tokens).")
                merged.setdefault("read", merged["input"] * 0.1)
                merged.setdefault("cw5m", merged["input"])
                merged.setdefault("cw1h", merged["input"])
                pricing[model] = merged
            break
    return pricing


def load_units() -> dict:
    for c in (os.path.join(CONFIG_DIR, "units.json"),
              os.path.join(SKILL_DIR, "units.json")):
        if os.path.isfile(c):
            return load_user_json(c)
    return {}


def load_config() -> dict:
    """Optional ~/.claude/eod-review/config.json: {dev_roots:[...], personal:[...]}."""
    for c in (os.path.join(CONFIG_DIR, "config.json"),
              os.path.join(SKILL_DIR, "config.json")):
        if os.path.isfile(c):
            return load_user_json(c)
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


def parse_day(value: str, flag: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        sys.exit(f"{flag} {value!r} is not a date. Write it as YYYY-MM-DD, e.g. {dt.date.today()}.")


def local_date_bounds(since: str | None, until: str | None, days: int | None):
    today = dt.date.today()
    if days is not None:
        start = today - dt.timedelta(days=max(0, days - 1))
        end = today
    else:
        start = parse_day(since, "--since") if since else today
        end = parse_day(until, "--until") if until else today
    if start > end:
        sys.exit(f"--since {start} is after --until {end}. Swap them.")
    return start, end


def resolve_unit(args) -> dict:
    """Returns {path, branch, author, all_branches, all_authors, dev_roots,
    personal, unit_is_personal}."""
    unit = {}
    if args.unit:
        units = load_units()
        if args.unit not in units:
            sys.exit(f"Unknown unit '{args.unit}'. Defined: {', '.join(units) or '(none)'}. "
                     f"To see the setup run: python3 {os.path.join(SKILL_DIR, 'eod_review.py')} --check "
                     "(add --init to create a 'work' unit).")
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
    # Agent apps often commit under their own identity (T3 Code, a bot account).
    # config.json "authors" lists the other names or emails that are also you.
    authors = []
    if author:
        authors = [author] + ([] if args.author else
                              [a for a in (cfg.get("authors") or []) if a and a != author])
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

    return {"path": path, "branch": branch, "author": ", ".join(authors) or None,
            "authors": authors,
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
    # "Every branch" means local and remote branches. Not --all: that also walks
    # refs/stash and tool-private refs (agent checkpoints), which are not commits
    # anyone made.
    rev_args = ["--branches", "--remotes"] if unit["all_branches"] else \
        ["--end-of-options", unit["branch"] if unit["branch"] else "HEAD"]
    # git's --since/--until test the COMMITTER date, which a rebase, amend or
    # cherry-pick resets. The day a commit belongs to is the day it was written
    # (author date), so ask git for everything committed since the window opened
    # (a commit is never committed before it is written) and filter by author
    # date below.
    # format-local: every commit in this machine's timezone, the same clock the
    # token timestamps are read in. Options first; the rev goes last, after
    # --end-of-options, so a branch name can never be read as a git option.
    cmd = [
        "log",
        f"--since={start.isoformat()} 00:00:00",
        f"--pretty=format:{fmt}", "--date=format-local:%Y-%m-%d %H:%M",
    ]
    for who in unit.get("authors") or []:
        cmd.append(f"--author={who}")
    cmd += rev_args
    tag = os.path.basename(repo.rstrip("/"))
    commits = []
    for line in run_git(repo, *cmd).splitlines():
        if not line.strip():
            continue
        h, d, a, s = (line.split("\x1f") + ["", "", "", ""])[:4]
        if not start.isoformat() <= d[:10] <= end.isoformat():
            continue
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
    """The row a model's tokens go in: its own id, tidied.

    "claude-opus-5-5-20260401" -> "opus-5-5"; "gpt-6-astra" stays as it is.
    Rows are per model, not per family, so each can carry its own price.
    """
    m = (model or "").lower().strip()
    if "synthetic" in m or not m:
        return "synthetic"
    m = m.split("@")[0].split("[")[0]
    m = re.sub(r"^(us\.|eu\.|global\.)?anthropic[./]", "", m)
    m = re.sub(r"^claude-", "", m)
    m = re.sub(r"-(20\d{6}|latest)$", "", m)
    return m[:32] or "synthetic"


def price_for(bucket: str, pricing: dict) -> dict | None:
    """Rates for a row: its exact key, else the longest key it starts with."""
    if bucket in pricing:
        return pricing[bucket]
    # Only rows the user added match by prefix; a built-in row prices its own model and no other.
    keys = [k for k in pricing if k not in DEFAULT_PRICING and bucket.startswith(k)]
    return pricing[max(keys, key=len)] if keys else None


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
    # Claude Code writes one line per content block, so one API reply appears on
    # several lines with the same message id and the same usage, and a resumed or
    # forked session copies earlier lines into a new file. Count each reply once:
    # keep the line with the most output (earlier lines of a streamed reply can
    # carry a partial count).
    seen: dict = {}
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

                key = (msg.get("id"), o.get("requestId"))
                if key == (None, None):
                    key = (f, len(seen))
                held = seen.get(key)
                if held and (held[2].get("output_tokens") or 0) >= (usage.get("output_tokens") or 0):
                    continue
                seen[key] = (ncwd, model_bucket(msg.get("model")), usage)
    ACTIVITY.clear()
    for ncwd, bucket, usage in seen.values():
        add_usage(sink_for(work, personal, ncwd, unit), bucket, usage)
        repo = repo_of(ncwd, unit["dev_roots"])
        if repo:
            ACTIVITY[repo] = ACTIVITY.get(repo, 0) + 1
    return work, personal


# Claude Code turns per repo folder in the last collect_tokens() window.
ACTIVITY: dict = {}


_REPO_ROOT_CACHE: dict = {}


def repo_of(ncwd: str | None, dev_roots: list) -> str | None:
    """The git repo a session ran in: the nearest folder with a .git, looking up
    from the session's folder and stopping at the dev root. A session outside any
    repo is filed under the first folder below the dev root."""
    if not ncwd:
        return None
    for root in dev_roots:
        root = root.rstrip("/")
        if not ncwd.startswith(root + "/"):
            continue
        if ncwd in _REPO_ROOT_CACHE:
            return _REPO_ROOT_CACHE[ncwd]
        found = None
        folder = ncwd
        while folder != root and folder.startswith(root + "/"):
            if os.path.exists(os.path.join(folder, ".git")):
                found = folder
                break
            folder = os.path.dirname(folder)
        found = found or os.path.join(root, ncwd[len(root) + 1:].split("/")[0])
        _REPO_ROOT_CACHE[ncwd] = found
        return found
    return None


def summarize_activity(unit: dict, commits: list, personal_commits: list,
                       start: dt.date, end: dt.date) -> list[dict]:
    """Projects with Claude Code sessions in the window, next to what git shows.

    A day's work is not always a commit: a project can have a hundred agent turns
    and only uncommitted files, or commits made under another identity. Those
    would be missing from a commits-only report, so each one is listed with the
    reason. Each row carries the same `personal` flag and `group` name the rest
    of the report uses, so it can be kept in its own section. Only Claude Code
    records where a session ran in enough detail for this list. Busiest first.
    """
    counted: dict = {}
    for c in list(commits) + list(personal_commits):
        counted[c.get("repo")] = counted.get(c.get("repo"), 0) + 1
    rows = []
    for repo, turns in sorted(ACTIVITY.items(), key=lambda kv: -kv[1]):
        name = os.path.basename(repo)
        row = {"repo": name, "turns": turns, "commits": counted.get(name, 0)}
        if not unit["unit_is_personal"] and is_personal(repo, unit["personal"], unit["dev_roots"]):
            row["personal"] = True
        group = group_of(repo, unit)
        if group:
            row["group"] = group
        if not is_git_repo(repo):
            row["not_a_git_repo"] = True
        else:
            # --no-optional-locks: look, never refresh the repo's index.
            status = run_git(repo, "--no-optional-locks", "status", "--porcelain").splitlines()
            row["uncommitted_files"] = len(status)
            # A sample of what changed, so work with no commit can still be described.
            row["changed"] = [line[2:].strip() for line in status[:15]]
            if not row["commits"] and not unit["all_authors"]:
                others: dict = {}
                log = run_git(repo, "log", "--branches", "--remotes",
                              f"--since={start.isoformat()} 00:00:00",
                              "--pretty=format:%ae%x1f%ad", "--date=format-local:%Y-%m-%d")
                for line in log.splitlines():
                    email, _, day = line.partition("\x1f")
                    if start.isoformat() <= day <= end.isoformat():
                        others[email] = others.get(email, 0) + 1
                if others:
                    row["commits_by_other_authors"] = others
        rows.append(row)
    return rows


def render_activity(lines: list, report: dict) -> None:
    rows = [r for r in report.get("activity") or [] if not r["commits"]]
    if not rows:
        return
    lines.append("\nWORKED ON, NOT IN THE COMMITS ABOVE")
    for r in rows:
        if r.get("not_a_git_repo"):
            why = "not a git repo"
        elif r.get("commits_by_other_authors"):
            why = "commits by " + ", ".join(f"{k} ({v})" for k, v in r["commits_by_other_authors"].items()) \
                + f", {r.get('uncommitted_files', 0)} uncommitted files"
        else:
            why = f"{r.get('uncommitted_files', 0)} uncommitted files, no commits"
        tag = "(personal) " if r.get("personal") else f"({r['group']}) " if r.get("group") else ""
        lines.append(f"  {tag + r['repo']:<28} {r['turns']:>5} Claude Code turns   {why}")


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
        model: str | None = None
        seen_totals: set = set()
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
                    model = payload.get("model") or model
                    continue
                if kind != "event_msg" or payload.get("type") != "token_count":
                    continue
                d = parse_local_date(o.get("timestamp"))
                if d is None or d < start or d > end:
                    continue
                ncwd = normalize_cwd(cwd, unit["dev_roots"])
                if not path_matches(ncwd, unit["path"]):
                    continue

                info = payload.get("info") or {}
                last = info.get("last_token_usage") or {}
                # Codex sometimes repeats an event with an unchanged running total.
                running = json.dumps(info.get("total_token_usage"), sort_keys=True)
                if info.get("total_token_usage") and running in seen_totals:
                    continue
                seen_totals.add(running)
                inp = last.get("input_tokens", 0)
                cached = last.get("cached_input_tokens", 0)
                b = sink_for(work, personal, ncwd, unit).setdefault(
                    model_bucket(model or "gpt"), empty_bucket())
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
    # Same one-line-per-content-block format as Claude Code, so the same rule:
    # one reply is counted once, from the line with the most output.
    seen: dict = {}
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
                key = (msg.get("id"), o.get("requestId"))
                if key == (None, None):
                    key = (f, len(seen))
                held = seen.get(key)
                if held and (held[2].get("output_tokens") or 0) >= (usage.get("output_tokens") or 0):
                    continue
                seen[key] = (sink, model_bucket(msg.get("model")), usage)
    for sink, bucket, usage in seen.values():
        add_usage(sink, bucket, usage)
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
            model_bucket(o.get("modelID") or "unknown-model"), empty_bucket())
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


# Which of the other agents put tokens in the last collect_other_agents() run.
CONTRIBUTED_OTHER: list = []


def collect_other_agents(unit: dict, start: dt.date, end: dt.date, skip: set) -> tuple:
    """Everything beyond Claude Code, Codex, Grok and Cowork.

    Returns ((work, personal) token split, sessions, included) where `sessions`
    holds agents that keep no token counts ({"cursor": {"sessions": 3}}) and
    `included` lists the agents that were read.
    """
    split: tuple = ({}, {})
    sessions: dict = {}
    included = [a for a in OTHER_AGENTS if a not in skip]
    CONTRIBUTED_OTHER.clear()
    if "gemini" in included:
        found_tokens = collect_gemini_tokens(unit, start, end)
        if has_tokens(found_tokens):
            CONTRIBUTED_OTHER.append("Gemini CLI")
        split = merge_split(split, found_tokens)
    if "opencode" in included:
        found_tokens = collect_opencode_tokens(unit, start, end)
        if has_tokens(found_tokens):
            CONTRIBUTED_OTHER.append("opencode")
        split = merge_split(split, found_tokens)
    if "cursor" in included:
        found = count_cursor_sessions(unit, start, end)
        if found:
            sessions["cursor"] = found
    if "antigravity" in included:
        found = count_antigravity_sessions(unit, start, end)
        if found:
            sessions["antigravity"] = found
    return split, sessions, included



def cost_of(bucket_name: str, b: dict, pricing: dict) -> float | None:
    """Estimated USD for a row, or None when the model has no price."""
    if bucket_name == "synthetic":
        return 0.0
    r = price_for(bucket_name, pricing)
    if r is None:
        return None
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
    unpriced: dict = {}
    total_cost = 0.0
    for name, b in by_model.items():
        for k in totals:
            totals[k] += b[k]
        c = cost_of(name, b, pricing)
        if c is None:
            unpriced[name] = b["input"] + b["cw5m"] + b["cw1h"] + b["cw_other"] + b["read"] + b["output"]
            models[name] = {**b, "cost_usd": None}
            continue
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
        # Models with no price row: their tokens are in the totals, their cost is not.
        "unpriced": unpriced,
        "prices_as_of": PRICES_AS_OF,
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


def has_tokens(split: tuple) -> bool:
    """True when a collector's (work, personal) pair holds any usage at all."""
    return any(b.get("calls") for part in split for b in part.values())


def sources_note(report: dict) -> str:
    # Only sources that put tokens in THIS report are named. One that was read
    # and found nothing is left out, so the header never claims data it lacks.
    extra = list(report.get("contributed") or [])
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
    lines.append(f"  cache reads:        {human(t['cache_read'])}")
    lines.append(f"  grand total:        {human(t['grand_total'])}")
    lines.append("\n  per model:")
    for name, b in sorted(tk["by_model"].items(), key=lambda kv: -kv[1]["output"]):
        fi = b["input"] + b["cw5m"] + b["cw1h"] + b["cw_other"]
        cost = "unpriced" if b["cost_usd"] is None else f"${b['cost_usd']:.2f}"
        lines.append(
            f"    {name:18} out={human(b['output']):>8}  "
            f"in={human(fi):>8}  read={human(b['read']):>8}  {cost}"
        )
    lines.append(f"\n  est. cost: ${tk['cost_usd_estimate']:.2f}  "
                 f"(ESTIMATE at Anthropic API list prices of {tk.get('prices_as_of', PRICES_AS_OF)}, not billed cost)")
    if tk.get("unpriced"):
        lines.append("  not in that figure: " + ", ".join(
            f"{name} ({human(n)} tokens)" for name, n in tk["unpriced"].items())
            + ". Add their rates to pricing.json to price them.")


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
    render_activity(lines, report)
    render_groups(lines, report)
    render_sessions(lines, report)
    render_personal(lines, report)
    lines.append("=" * 64)
    return "\n".join(lines)


# ------------------------------ first run ---------------------------------- #


def _newest(paths: list) -> str | None:
    """ISO date of the most recently changed file among `paths`, if any exist."""
    stamps = [os.path.getmtime(p) for p in paths if os.path.exists(p)]
    return dt.date.fromtimestamp(max(stamps)).isoformat() if stamps else None


def _grok_has_usage() -> bool:
    """Grok's log exists on every install; only inference records carry tokens."""
    try:
        with open(GROK_LOG) as fh:
            return any('"shell.turn.inference_done"' in line for line in fh)
    except OSError:
        return False


def detect_agents() -> list[dict]:
    """Which agents have left data on this machine, and how fresh it is."""
    def files(*pattern):
        return glob.glob(os.path.join(*pattern), recursive=True)
    rows = [
        ("Claude Code", "tokens", files(PROJECTS_DIR, "**", "*.jsonl")),
        ("Codex", "tokens", files(CODEX_DIR, "sessions", "**", "*.jsonl")
            + files(CODEX_DIR, "archived_sessions", "**", "*.jsonl")),
        ("Grok", "tokens", [GROK_LOG] if _grok_has_usage() else []),
        ("Cowork", "tokens", [f for root in COWORK_ROOTS for f in files(root, "**", "*.jsonl")]),
        ("Gemini CLI", "tokens", files(GEMINI_DIR, "tmp", "*", "chats", "*.json")),
        ("opencode", "tokens", [OPENCODE_DB]),
        ("Cursor", "sessions only", [CURSOR_DB, CURSOR_DB_LINUX]),
        ("Antigravity", "sessions only", [ANTIGRAVITY_DB]),
    ]
    return [{"agent": name, "reads": reads, "last_data": _newest(paths)}
            for name, reads, paths in rows]


def check_setup() -> dict:
    """Everything a first run needs to know, without writing anything."""
    cfg = load_config()
    dev_roots = [os.path.abspath(os.path.expanduser(r))
                 for r in (cfg.get("dev_roots") or DEV_ROOTS_DEFAULT)]
    roots = [{"path": r, "exists": os.path.isdir(r),
              "repos": len(discover_repos(r)) if os.path.isdir(r) else 0} for r in dev_roots]
    files = {n: os.path.isfile(os.path.join(CONFIG_DIR, n))
             for n in ("config.json", "units.json", "style.md")}
    email = run_git(HOME, "config", "--global", "user.email") or None
    cutoff = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    agents = detect_agents()
    problems = []
    if not shutil.which("git"):
        problems.append("git is not installed, so no commits can be read.")
    if not email:
        problems.append("git has no global user.email, so commits cannot be filtered to yours. "
                        "Set it with: git config --global user.email you@example.com")
    if not any(r["repos"] for r in roots):
        problems.append("No git repos found under " + ", ".join(dev_roots) +
                        '. Put your code folder in config.json as "dev_roots".')
    if not any(a["last_data"] for a in agents):
        problems.append("No agent data found. Reports will list commits with no tokens or cost.")
    for a in agents:
        if a["last_data"] and a["last_data"] < cutoff:
            a["stale"] = True
    return {"config_dir": CONFIG_DIR, "files": files, "dev_roots": roots,
            "author": email, "units": sorted(k for k in load_units() if not k.startswith("_")),
            "voice": cfg.get("voice"), "agents": agents, "problems": problems,
            "ready": all(files[n] for n in ("config.json", "units.json")) and not problems}


def render_check(c: dict) -> str:
    lines = ["STANDUP SETUP CHECK", f"  config folder: {c['config_dir']}"]
    for name, there in c["files"].items():
        lines.append(f"    {name:<12} {'found' if there else 'missing'}")
    lines.append(f"  your commits:  {c['author'] or '(no git user.email)'}")
    lines.append("  code folders:")
    for r in c["dev_roots"]:
        lines.append(f"    {r['path']}  " + (f"{r['repos']} repos" if r["exists"] else "does not exist"))
    lines.append(f"  units:         {', '.join(c['units']) or '(none)'}")
    lines.append("  agents:")
    for a in c["agents"]:
        state = (f"last data {a['last_data']}" + (" (over 30 days old)" if a.get("stale") else "")
                 if a["last_data"] else "no data on this machine")
        lines.append(f"    {a['agent']:<12} {a['reads']:<14} {state}")
    for problem in c["problems"]:
        lines.append(f"  PROBLEM: {problem}")
    lines.append("  " + ("Ready." if c["ready"] else "Not set up yet. Run with --init to write the missing files."))
    return "\n".join(lines)


def init_setup() -> list[str]:
    """Write the missing config files. Never overwrites one that exists."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    roots = [r for r in DEV_ROOTS_DEFAULT if os.path.isdir(r)]
    tilde = lambda p: "~" + p[len(HOME):] if p.startswith(HOME) else p
    wrote = []

    def write(name: str, text: str) -> None:
        path = os.path.join(CONFIG_DIR, name)
        if os.path.exists(path):
            return
        with open(path, "w") as fh:
            fh.write(text)
        wrote.append(path)

    write("config.json", json.dumps(
        {"dev_roots": [tilde(r) for r in roots], "groups": {}, "personal": []}, indent=2) + "\n")
    if roots:
        write("units.json", json.dumps(
            {"work": {"path": tilde(roots[0]), "all_branches": True}}, indent=2) + "\n")
    example = os.path.join(SKILL_DIR, "style.example.md")
    if os.path.isfile(example):
        with open(example) as fh:
            write("style.md", fh.read())
    return wrote


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
    p.add_argument("--check", action="store_true",
                   help="first run: show config, code folders and which agents have data; writes nothing")
    p.add_argument("--init", action="store_true",
                   help="first run: write the missing config files, then show --check")
    args = p.parse_args()

    if args.check or args.init:
        wrote = init_setup() if args.init else []
        check = check_setup()
        if args.json:
            print(json.dumps({**check, "wrote": wrote}, indent=2))
        else:
            for path in wrote:
                print(f"wrote {path}")
            print(render_check(check))
        return

    unit = resolve_unit(args)
    start, end = local_date_bounds(args.since, args.until, args.days)
    pricing = load_pricing(args.pricing)

    commits, personal_commits = collect_commits(unit, start, end)
    split = collect_tokens(unit, start, end)
    includes_codex = not args.no_codex
    includes_grok = not args.no_grok
    includes_cowork = not args.no_cowork
    contributed = []
    for wanted, label, collect in ((includes_codex, "Codex", collect_codex_tokens),
                                   (includes_grok, "Grok", collect_grok_tokens),
                                   (includes_cowork, "Cowork", collect_cowork_tokens)):
        if not wanted:
            continue
        found = collect(unit, start, end)
        if has_tokens(found):
            contributed.append(label)
        split = merge_split(split, found)
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
        # Sources that actually put tokens in this report (the includes_* flags
        # only say which were looked at).
        "contributed": contributed + list(CONTRIBUTED_OTHER),
        "sessions": sessions,
        "activity": summarize_activity(unit, commits, personal_commits, start, end),
    }
    if by_group:
        report["by_group"] = by_group

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))


if __name__ == "__main__":
    main()
