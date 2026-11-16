#!/usr/bin/env python3
"""EOW review engine: commits + Claude Code token usage for one ISO week.

A thin *weekly* wrapper around the EOD engine. It does two things the daily
engine doesn't:

1. Computes the current week's **Monday -> Sunday** window deterministically
   (real system date, no LLM date math), with an optional ``--week-offset`` so
   "last week" is ``--week-offset -1``.
2. Adds a **per-day commit breakdown**, derived from the single weekly commit
   list, so the recap can show what shipped on which day without extra git or
   transcript reads.

Everything else — commit collection, token attribution by worktree+branch+day,
the editable pricing table, and the shared ``units.json`` — is imported from
``eod_review.py`` so the two reviews never drift apart.

Cost is an ESTIMATE from the same editable price table and is labelled as such —
never quote it as billed cost.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

# Reuse the EOD engine as the single source of truth for collection, pricing,
# and unit resolution (incl. the shared ~/.claude/eod-review/units.json).
# Looked up next to this skill first (works wherever the pair is installed),
# then in the default personal skills folder.
_HERE = os.path.dirname(os.path.abspath(__file__))
EOD_SKILL_DIR = next(
    (d for d in (os.path.join(os.path.dirname(_HERE), "eod-review"),
                 os.path.join(os.path.expanduser("~"), ".claude", "skills", "eod-review"))
     if os.path.isfile(os.path.join(d, "eod_review.py"))),
    os.path.join(os.path.dirname(_HERE), "eod-review"))
if EOD_SKILL_DIR not in sys.path:
    sys.path.insert(0, EOD_SKILL_DIR)

try:
    from eod_review import (  # noqa: E402
        resolve_unit,
        load_pricing,
        collect_commits,
        collect_tokens,
        collect_codex_tokens,
        collect_grok_tokens,
        collect_cowork_tokens,
        collect_other_agents,
        parse_skip,
        merge_split,
        summarize_tokens,
        summarize_groups,
        human,
        sources_note,
        render_commit,
        render_token_block,
        render_personal,
        render_sessions,
        render_groups,
    )
except Exception as exc:  # pragma: no cover - import guard
    sys.exit(
        "eow-review: could not import the eod-review engine from "
        f"{EOD_SKILL_DIR}: {exc}"
    )


# ------------------------------ week window -------------------------------- #


def week_bounds(today: dt.date, offset: int) -> tuple[dt.date, dt.date]:
    """Monday -> Sunday for the week containing ``today``, shifted by ``offset`` weeks.

    weekday(): Monday == 0 ... Sunday == 6. So ``today - weekday`` is this week's
    Monday; +6 days is Sunday. ``offset`` shifts whole weeks (-1 == last week).
    """
    monday = today - dt.timedelta(days=today.weekday()) + dt.timedelta(weeks=offset)
    sunday = monday + dt.timedelta(days=6)
    return monday, sunday


def group_commits_by_day(commits: list[dict], start: dt.date, end: dt.date) -> dict:
    """Bucket the weekly commit list by ISO date, with every day present (even empty)."""
    days: dict[str, list[dict]] = {}
    cur = start
    while cur <= end:
        days[cur.isoformat()] = []
        cur += dt.timedelta(days=1)
    for c in commits:
        day = (c.get("date") or "")[:10]
        days.setdefault(day, []).append(c)
    return days


# ------------------------------- rendering --------------------------------- #


def render_text(report: dict) -> str:
    u, w = report["unit"], report["window"]
    lines = []
    lines.append("=" * 64)
    lines.append(f"EOW REVIEW  (week {w['week']}, {w['year']})")
    scope = f"branch={u['branch'] or '(all)'}  author={u['author'] or '(all)'}"
    lines.append(f"  worktree: {u['path']}")
    lines.append(f"  {scope}")
    lines.append(f"  window:   {w['start']} -> {w['end']}  (Mon -> Sun)")
    lines.append("=" * 64)

    commits = report["commits"]
    lines.append(f"\nCOMMITS ({len(commits)})  by day")
    for day, day_commits in report["by_day"].items():
        weekday = dt.date.fromisoformat(day).strftime("%a")
        lines.append(f"\n  {weekday} {day}  ({len(day_commits)})")
        for c in day_commits:
            time = (c.get("date") or "")[11:] or "--:--"
            repo = f"[{c['repo']}] " if c.get("repo") else ""
            if c.get("group"):
                repo = f"({c['group']}) {repo}"
            lines.append(f"    {time}  {c['hash']}  {repo}{c['subject']}")
        if not day_commits:
            lines.append("    (none)")
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
    p = argparse.ArgumentParser(
        description="EOW review: commits + token usage for one ISO week (Mon -> Sun)."
    )
    p.add_argument("--unit", help="named work unit from units.json (shared with eod-review)")
    p.add_argument("--path", help="worktree path (default: cwd)")
    p.add_argument("--branch", help="git branch (default: current)")
    p.add_argument("--author", help="commit/author filter email (default: git config user.email)")
    p.add_argument("--week-offset", type=int, default=0,
                   help="whole-week shift: 0=current week, -1=last week, etc.")
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
    start, end = week_bounds(dt.date.today(), args.week_offset)
    pricing = load_pricing(args.pricing)

    commits, personal_commits = collect_commits(unit, start, end)
    by_day = group_commits_by_day(commits, start, end)
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

    iso_year, iso_week, _ = start.isocalendar()
    report = {
        "unit": unit,
        "window": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "week": iso_week,
            "year": iso_year,
        },
        "commits": commits,
        "personal_commits": personal_commits,
        "by_day": by_day,
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
