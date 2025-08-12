from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List
from .schemas import ActionItem


def to_ics(title: str, actions: List[ActionItem], outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "tasks.ics"
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//meeting-copilot//EN"]
    for i, a in enumerate(actions, start=1):
        if not a.due:
            continue
        uid = f"task-{i}-{int(datetime.utcnow().timestamp())}@meeting-copilot"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART;VALUE=DATE:{a.due.strftime('%Y%m%d')}",
            f"SUMMARY:{title} — {a.owner}: {a.task}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
