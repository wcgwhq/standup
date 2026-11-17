#!/usr/bin/env python3
"""Standup engine, a week, a month or a range: commits + Claude Code token usage for one ISO week.

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
``standup.py`` so the two reviews never drift apart.

Cost is an ESTIMATE from the same editable price table and is labelled as such —
never quote it as billed cost.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

# Reuse the day engine as the single source of truth for collection, pricing and unit
# resolution (incl. the shared ~/.claude/standup/units.json). It is the file next to this one.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from standup import (  # noqa: E402
        resolve_unit,
        parse_day,
        load_pricing,
        collect_commits,
        collect_tokens,
        collect_codex_tokens,
        collect_grok_tokens,
        collect_cowork_tokens,
        collect_other_agents,
        CONTRIBUTED_OTHER,
        has_tokens,
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
        summarize_activity,
        render_activity,
    )
except Exception as exc:  # pragma: no cover - import guard
    sys.exit(
        "standup: could not import the engine (standup.py) from "
        f"{_HERE}: {exc}"
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


def month_bounds(today: dt.date, value: str) -> tuple[dt.date, dt.date]:
    """First -> last day of a month. ``value`` is "this", "last" or "YYYY-MM"."""
    if value == "this":
        year, month = today.year, today.month
    elif value == "last":
        year, month = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
    else:
        try:
            year, month = (int(x) for x in value.split("-"))
            dt.date(year, month, 1)
        except ValueError:
            sys.exit(f"--month {value!r} is not a month. Write it as YYYY-MM, e.g. "
                     f"{today:%Y-%m}, or use 'this' or 'last'.")
    first = dt.date(year, month, 1)
    return first, (first.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)


def group_commits_by_day(commits: list[dict], start: dt.date, end: dt.date) -> dict:
    """Bucket the weekly commit list by ISO date, with every day present (even empty)."""
    days: dict[str, list[dict]] = {}
    cur = start
    while cur <= end:
        days[cur.isoformat()] = []
        cur += dt.timedelta(days=1)
    for c in commits:
        day = (c.get("date") or "")[:10]
        if day in days:
            days[day].append(c)
    return days


# ------------------------------- rendering --------------------------------- #


def render_text(report: dict) -> str:
    u, w = report["unit"], report["window"]
    lines = []
    lines.append("=" * 64)
    week_long = w["kind"] == "week"
    lines.append({"week": f"STANDUP  (week {w['week']}, {w['year']})",
                  "month": f"MONTH REVIEW  ({w['label']})",
                  "range": f"RANGE REVIEW  ({w['days']} days)"}[w["kind"]])
    scope = f"branch={u['branch'] or '(all)'}  author={u['author'] or '(all)'}"
    lines.append(f"  worktree: {u['path']}")
    lines.append(f"  {scope}")
    lines.append(f"  window:   {w['start']} -> {w['end']}" + ("  (Mon -> Sun)" if week_long else ""))
    lines.append("=" * 64)

    commits = report["commits"]
    lines.append(f"\nCOMMITS ({len(commits)})  by day")
    lines_week = None
    for day, day_commits in report["by_day"].items():
        # A week shows all seven days. A month or a range shows the days with commits,
        # under a heading for each ISO week.
        if not week_long:
            if not day_commits:
                continue
            week = dt.date.fromisoformat(day).isocalendar()[1]
            if week != lines_week:
                lines_week = week
                lines.append(f"\n  -- week {week} --")
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
    render_activity(lines, report)
    render_groups(lines, report)
    render_sessions(lines, report)
    render_personal(lines, report)
    lines.append("=" * 64)
    return "\n".join(lines)


# --------------------------------- main ------------------------------------ #


def main() -> None:
    p = argparse.ArgumentParser(
        description="Standup: commits + token usage for one ISO week (Mon -> Sun)."
    )
    p.add_argument("--unit", help="named work unit from units.json (shared with the day report)")
    p.add_argument("--path", help="worktree path (default: cwd)")
    p.add_argument("--branch", help="git branch (default: current)")
    p.add_argument("--author", help="commit/author filter email (default: git config user.email)")
    p.add_argument("--week-offset", type=int, default=0,
                   help="whole-week shift: 0=current week, -1=last week, etc.")
    p.add_argument("--month", nargs="?", const="this", metavar="YYYY-MM",
                   help="a whole calendar month instead of a week: YYYY-MM, 'this' (default) or 'last'")
    p.add_argument("--since", help="start of a custom range YYYY-MM-DD (use with --until)")
    p.add_argument("--until", help="end of a custom range YYYY-MM-DD (default: today)")
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
    today = dt.date.today()
    if args.since or args.until:
        if args.month or args.week_offset:
            sys.exit("Pick one window: --since/--until, --month or --week-offset.")
        if not args.since:
            sys.exit("--until needs --since: the range has to start somewhere.")
        kind = "range"
        start, end = parse_day(args.since, "--since"), parse_day(args.until, "--until") if args.until else today
        if start > end:
            sys.exit(f"--since {start} is after --until {end}. Swap them.")
    elif args.month:
        if args.week_offset:
            sys.exit("Pick one window: --month or --week-offset.")
        kind = "month"
        start, end = month_bounds(today, args.month)
    else:
        kind = "week"
        start, end = week_bounds(today, args.week_offset)
    pricing = load_pricing(args.pricing)

    commits, personal_commits = collect_commits(unit, start, end)
    by_day = group_commits_by_day(commits, start, end)
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

    iso_year, iso_week, _ = start.isocalendar()
    report = {
        "unit": unit,
        "window": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "week": iso_week,
            "year": iso_year,
            "kind": kind,
            "label": f"{start:%B %Y}" if kind == "month" else None,
            "days": (end - start).days + 1,
            # Days after today are in the window but have not happened yet.
            "complete": end <= today,
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
