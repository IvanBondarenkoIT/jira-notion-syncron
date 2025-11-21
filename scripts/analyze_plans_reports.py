#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger
from rapidfuzz import fuzz, process  # type: ignore

TRANSCRIPTS_DIR = Path("data/processed/transcripts")
ANALYSIS_DIR = Path("data/processed/analysis")


@dataclass
class Clip:
    basename: str
    date: Optional[str]
    time: Optional[str]
    backend: str
    text: str
    language: Optional[str]
    classification: str  # plan | report | unknown
    items: List[str]


KEYWORDS_PLAN = [
    "план", "планы", "запланировал", "запланирую", "собираюсь", "намерен", "сделать сегодня", "на сегодня", "на неделю",
]
KEYWORDS_REPORT = [
    "отчет", "отчёт", "сделал", "выполнил", "готово", "сделано", "результат", "итоги", "завершил",
]

SENTENCE_SPLIT_RE = re.compile(r"[\n\r]+|(?<=[\.!?;])\s+")
BULLET_RE = re.compile(r"^\s*(?:[-•*\u2022]|\d+[\.)])\s+")
WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    t = text.strip()
    t = WHITESPACE_RE.sub(" ", t)
    return t


def guess_classification(text: str, date_str: Optional[str], time_str: Optional[str]) -> str:
    # Weekly rule takes precedence: Monday -> plan, Friday -> report
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str)
            weekday = dt.weekday()  # Monday=0 ... Sunday=6
            if weekday == 0:
                return "plan"
            if weekday == 4:
                return "report"
        except Exception:
            pass

    # Fallback: keyword-based only (ignore time-of-day)
    t = text.lower()
    plan_score = sum(1 for k in KEYWORDS_PLAN if k in t)
    report_score = sum(1 for k in KEYWORDS_REPORT if k in t)

    if plan_score > report_score and plan_score > 0:
        return "plan"
    if report_score > plan_score and report_score > 0:
        return "report"
    return "unknown"


def extract_items(text: str) -> List[str]:
    lines = [l.strip(" -•*\u2022\t") for l in text.splitlines()]
    bullet_lines = [normalize_text(l) for l in lines if BULLET_RE.search("- " + l) or l.startswith(("-", "*", "•")) or re.match(r"^\d+[\.)]", l)]
    if bullet_lines:
        return [l for l in bullet_lines if len(l) > 2]

    sentences = [normalize_text(s) for s in re.split(r"[\.!?;\n]+", text) if normalize_text(s)]
    sentences = [s for s in sentences if len(s.split()) >= 3]
    return sentences


def load_transcripts() -> List[Clip]:
    if not TRANSCRIPTS_DIR.exists():
        logger.error("Transcripts directory does not exist: {}", TRANSCRIPTS_DIR)
        return []
    clips: List[Clip] = []
    for p in sorted(TRANSCRIPTS_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            meta = data.get("metadata", {})
            date = meta.get("date")
            time_str = meta.get("time")
            classification = guess_classification(data.get("text", ""), date, time_str)
            items = extract_items(data.get("text", ""))
            clips.append(
                Clip(
                    basename=meta.get("basename", p.stem),
                    date=date,
                    time=time_str,
                    backend=meta.get("backend", "unknown"),
                    text=data.get("text", ""),
                    language=data.get("language"),
                    classification=classification,
                    items=items,
                )
            )
        except Exception as e:
            logger.exception("Failed to parse {}: {}", p.name, e)
    return clips


def group_by_date(clips: List[Clip]) -> Dict[str, List[Clip]]:
    grouped: Dict[str, List[Clip]] = {}
    for c in clips:
        d = c.date or "unknown"
        grouped.setdefault(d, []).append(c)
    return grouped


def compare_items(plans: List[str], reports: List[str]) -> Tuple[List[Tuple[str, str, int]], List[str], List[str]]:
    matches: List[Tuple[str, str, int]] = []
    unmatched_reports = set(reports)

    for p in plans:
        if not p:
            continue
        candidate, score, _ = process.extractOne(p, reports, scorer=fuzz.token_set_ratio) or (None, 0, None)
        if candidate is not None and score >= 70:
            matches.append((p, candidate, score))
            if candidate in unmatched_reports:
                unmatched_reports.remove(candidate)
        else:
            matches.append((p, "", 0))

    missing = [p for p, r, s in matches if s < 70]
    extras = list(unmatched_reports)
    return matches, missing, extras


def save_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def render_md_per_day(date: str, plans: List[str], reports: List[str], matches: List[Tuple[str, str, int]], missing: List[str], extras: List[str]) -> str:
    lines: List[str] = []
    lines.append(f"## {date}")
    lines.append("")
    lines.append("### Планы (неделя, понедельник)")
    for it in plans:
        lines.append(f"- {it}")
    lines.append("")
    lines.append("### Отчеты (неделя, пятница)")
    for it in reports:
        lines.append(f"- {it}")
    lines.append("")
    lines.append("### Сопоставление")
    for p, r, s in matches:
        if s >= 70:
            lines.append(f"- ✅ {p} ⇄ {r} ({s}%)")
        else:
            lines.append(f"- ❌ {p} ⇄ (нет соответствия)")
    lines.append("")
    if missing:
        lines.append("#### Не выполнено / нет в отчете")
        for it in missing:
            lines.append(f"- {it}")
        lines.append("")
    if extras:
        lines.append("#### Не было в планах, но есть в отчете")
        for it in extras:
            lines.append(f"- {it}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    clips = load_transcripts()
    if not clips:
        logger.error("No transcripts to analyze. Run scripts/transcribe_videos.py first.")
        return 1

    by_date = group_by_date(clips)

    summary_md_parts: List[str] = ["# Сводка по планам и отчетам"]

    csv_lines: List[str] = ["date,type,item,match_score,matched_with"]

    for date, day_clips in sorted(by_date.items(), key=lambda kv: kv[0] or ""):
        plans_items: List[str] = []
        reports_items: List[str] = []

        for c in sorted(day_clips, key=lambda c: c.time or ""):
            if c.classification == "plan":
                plans_items.extend(c.items)
            elif c.classification == "report":
                reports_items.extend(c.items)

        matches, missing, extras = compare_items(plans_items, reports_items)

        out_json = ANALYSIS_DIR / f"{date or 'unknown'}.json"
        save_json(
            out_json,
            {
                "date": date,
                "plans": plans_items,
                "reports": reports_items,
                "matches": matches,
                "missing_from_reports": missing,
                "extras_in_reports": extras,
            },
        )

        day_md = render_md_per_day(date or "unknown", plans_items, reports_items, matches, missing, extras)
        summary_md_parts.append(day_md)

        for p, r, s in matches:
            if s >= 70:
                csv_lines.append(f"{date or ''},match,{p.replace(',', ' ')},{s},{r.replace(',', ' ')}")
            else:
                csv_lines.append(f"{date or ''},missing,{p.replace(',', ' ')},0,")
        for e in extras:
            csv_lines.append(f"{date or ''},extra,{e.replace(',', ' ')},,")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        (ANALYSIS_DIR / "summary.md").write_text("\n\n".join(summary_md_parts), encoding="utf-8")
    except PermissionError:
        logger.warning("summary.md is locked, saving to summary_new.md instead")
        (ANALYSIS_DIR / "summary_new.md").write_text("\n\n".join(summary_md_parts), encoding="utf-8")
    (ANALYSIS_DIR / "summary.csv").write_text("\n".join(csv_lines), encoding="utf-8")

    logger.info("Analysis complete. See {}", ANALYSIS_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
