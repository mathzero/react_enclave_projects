#!/usr/bin/env python3
"""Render the REACT datasets timeline as a standalone SVG."""

from __future__ import annotations

import csv
import html
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from textwrap import wrap


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "react_datasets_timeline.csv"
OUT_FILE = ROOT / "assets" / "react-datasets-timeline.svg"


@dataclass
class Study:
    dataset: str
    kind: str
    start: date
    end: date
    n_value: int
    n_label: str
    color: str
    precision: str
    relationship: str
    details: str
    source_note: str


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_studies() -> list[Study]:
    with DATA_FILE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            Study(
                dataset=row["dataset"],
                kind=row["kind"],
                start=parse_date(row["start"]),
                end=parse_date(row["end"]),
                n_value=int(row["n_value"]),
                n_label=row["n_label"],
                color=row["color"],
                precision=row["precision"],
                relationship=row["relationship"],
                details=row["details"],
                source_note=row["source_note"],
            )
            for row in reader
        ]


def month_index(day: date) -> int:
    return day.year * 12 + day.month - 1


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def text(x: float, y: float, body: str, size: int = 16, weight: int = 400,
         fill: str = "#1f2933", anchor: str = "start", extra: str = "") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{esc(body)}</text>'
    )


def rounded_rect(x: float, y: float, width: float, height: float, fill: str,
                 radius: float = 10, stroke: str | None = None,
                 stroke_width: float = 1, opacity: float = 1.0,
                 extra: str = "") -> str:
    stroke_attr = f' stroke="{stroke}" stroke-width="{stroke_width}"' if stroke else ""
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" '
        f'rx="{radius:.1f}" fill="{fill}" opacity="{opacity:.3f}"{stroke_attr} {extra}/>'
    )


def path(points: str, stroke: str, width: float = 1.5, fill: str = "none",
         opacity: float = 1.0, dash: str | None = None, extra: str = "") -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<path d="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
        f'opacity="{opacity:.3f}"{dash_attr} {extra}/>'
    )


def render_svg(studies: list[Study]) -> str:
    width, height = 1840, 1120
    margin_left, margin_right = 540, 130
    plot_top, plot_bottom = 255, 720
    plot_left, plot_right = margin_left, width - margin_right
    plot_width = plot_right - plot_left

    axis_start = date(2020, 1, 1)
    axis_end = date(2026, 12, 31)
    total_months = month_index(axis_end) - month_index(axis_start) + 1

    def x_for(day: date) -> float:
        return plot_left + (month_index(day) - month_index(axis_start)) / (total_months - 1) * plot_width

    rows = len(studies)
    row_gap = (plot_bottom - plot_top) / (rows - 1)
    bar_h = 30

    max_n = max(study.n_value for study in studies)

    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Timeline of REACT data assets</title>',
        '<desc id="desc">Horizontal timeline showing REACT-1, REACT-2, clinical, Long COVID, and follow-up data collection windows from 2020 to 2026.</desc>',
        '<defs>',
        '<marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth"><path d="M2,2 L10,6 L2,10 z" fill="#5f6c7b"/></marker>',
        '<filter id="shadow" x="-10%" y="-20%" width="130%" height="150%"><feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#0f172a" flood-opacity="0.11"/></filter>',
        '</defs>',
        '<style>',
        'text { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }',
        '.axis { font-size: 16px; fill: #52616f; }',
        '.small { font-size: 14px; fill: #52616f; }',
        '.tiny { font-size: 12px; fill: #6b7785; }',
        '</style>',
        rounded_rect(28, 28, width - 56, height - 56, "#fbfcfd", 28, "#d9e2ec", 1),
        text(70, 88, "REACT Data Assets: Fieldwork Timeline and Cohort Relationships", 32, 750, "#17212b"),
        text(70, 130, "Bars show data collection windows; circles show approximate cohort/sample size on a square-root scale.", 18, 400, "#52616f"),
        text(70, 160, "Follow-up studies are subsets of the original REACT respondent base, with linkage governed by participant consent.", 18, 400, "#52616f"),
    ]

    # Plot area grid.
    svg.append(rounded_rect(plot_left - 16, plot_top - 58, plot_width + 32, plot_bottom - plot_top + 116, "#ffffff", 18, "#e6edf3", 1, extra='filter="url(#shadow)"'))
    for year in range(2020, 2027):
        x = x_for(date(year, 1, 1))
        svg.append(path(f"M{x:.1f},{plot_top - 34:.1f} L{x:.1f},{plot_bottom + 54:.1f}", "#d9e2ec", 1))
        svg.append(text(x, plot_bottom + 83, str(year), 16, 650, "#52616f", "middle"))
    svg.append(path(f"M{plot_left:.1f},{plot_bottom + 42:.1f} L{plot_right:.1f},{plot_bottom + 42:.1f}", "#9fb3c8", 1.5))

    # A light band for the pandemic surveillance period covered by the original respondent base.
    svg.append(rounded_rect(x_for(date(2020, 4, 1)), plot_top - 42, x_for(date(2022, 3, 31)) - x_for(date(2020, 4, 1)), plot_bottom - plot_top + 84, "#f1f5f9", 10, opacity=0.72))
    svg.append(text(x_for(date(2021, 4, 1)), plot_top - 18, "Original REACT pandemic surveillance period", 14, 650, "#6b7785", "middle"))

    # Rows and bars.
    baseline_y = plot_top
    for idx, study in enumerate(studies):
        y = plot_top + idx * row_gap
        x0, x1 = x_for(study.start), x_for(study.end)
        bar_y = y - bar_h / 2
        is_baseline = idx == 0
        opacity = 1.0 if is_baseline else 0.88
        bar_height = 38 if is_baseline else bar_h

        svg.append(path(f"M{plot_left - 8:.1f},{y:.1f} L{plot_right + 8:.1f},{y:.1f}", "#edf2f7", 1))
        if study.precision == "year":
            svg.append(rounded_rect(x0, bar_y - 2, max(12, x1 - x0), bar_height, study.color, 9, opacity=0.17))
            svg.append(rounded_rect(x0, bar_y + 4, max(12, x1 - x0), bar_height - 12, study.color, 7, stroke=study.color, stroke_width=2, opacity=0.55, extra='stroke-dasharray="7 6"'))
        else:
            svg.append(rounded_rect(x0, bar_y, max(12, x1 - x0), bar_height, study.color, 9, opacity=opacity))

        circle_r = 10 + math.sqrt(study.n_value / max_n) * 34
        circle_x = min(x1 + circle_r + 18, plot_right - circle_r - 6)
        svg.append(f'<circle cx="{circle_x:.1f}" cy="{y:.1f}" r="{circle_r:.1f}" fill="{study.color}" opacity="0.18"/>')
        svg.append(f'<circle cx="{circle_x:.1f}" cy="{y:.1f}" r="{max(6, circle_r * 0.42):.1f}" fill="{study.color}" opacity="0.78"/>')

        svg.append(text(70, y - 10, study.dataset, 18, 720 if is_baseline else 650, "#17212b"))
        svg.append(text(70, y + 17, f"{study.kind} | {study.n_label}", 14, 600, study.color))

        bar_label = f"{study.start.strftime('%b %Y')} to {study.end.strftime('%b %Y')}"
        if study.precision == "year":
            bar_label = f"{study.start.year} to {study.end.year} (year-level)"
        if (x1 - x0) < 275:
            svg.append(text(x0 + 4, y - 24, bar_label, 14, 700, study.color))
        else:
            svg.append(text(x0 + 14, y + 6, bar_label, 14, 700, "#ffffff" if study.precision != "year" else "#17212b"))

        if study.relationship:
            # Show subset relationship back to the baseline row.
            hook_x = x0 - 18
            svg.append(path(
                f"M{hook_x:.1f},{baseline_y + 20:.1f} C{hook_x - 36:.1f},{baseline_y + 70:.1f} {hook_x - 36:.1f},{y - 46:.1f} {hook_x:.1f},{y - 20:.1f}",
                "#5f6c7b",
                1.4,
                opacity=0.42,
                dash="4 5",
                extra='marker-end="url(#arrow)"',
            ))

    # Right-side notes.
    note_x, note_y = 70, 820
    svg.append(text(note_x, note_y, "Linkage and consent notes", 20, 750, "#17212b"))
    note_lines = [
        "Project note: around 80% of original respondents have linked NHS hospitalisation and GP data.",
        "Published 2022 follow-up frame: 2,494,309 of 3,099,386 adults (80.5%) consented to both recontact and routine health-record linkage.",
        "Clinical cohort participants consented for linkage; follow-up studies should be treated as linkable where the participant consent covers linkage.",
    ]
    cursor_y = note_y + 34
    for line in note_lines:
        wrapped = wrap(line, width=94)
        svg.append(f'<circle cx="{note_x + 8:.1f}" cy="{cursor_y - 5:.1f}" r="5" fill="#2a9d8f"/>')
        for line_no, wrapped_line in enumerate(wrapped):
            svg.append(text(note_x + 24, cursor_y + line_no * 19, wrapped_line, 15, 450, "#344054"))
        cursor_y += 24 + len(wrapped) * 19

    source_x, source_y = 1015, 820
    svg.append(text(source_x, source_y, "Source context used", 20, 750, "#17212b"))
    sources = [
        "Imperial REACT study pages: REACT-1, REACT-2, REACT Long COVID, REACT GE/LC Clinical, and REACT follow-up survey.",
        "Atchison et al., Nature Communications 2023: REACT-1/2 fieldwork windows, 2022 Long COVID invitation dates, response counts, and linkage-consent frame.",
        "User-provided project notes: initial N~3.5M, 2025 new cohort N~800k, and linkage status assumptions.",
    ]
    cursor_y = source_y + 34
    for source in sources:
        wrapped = wrap(source, width=72)
        for line_no, line in enumerate(wrapped):
            svg.append(text(source_x, cursor_y + line_no * 18, line, 14, 450, "#52616f"))
        cursor_y += 23 + len(wrapped) * 18

    svg.append(text(width - 70, height - 48, "Generated from data/react_datasets_timeline.csv", 12, 500, "#8294a8", "end"))
    svg.append("</svg>")
    return "\n".join(svg)


def main() -> None:
    studies = load_studies()
    OUT_FILE.write_text(render_svg(studies), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
