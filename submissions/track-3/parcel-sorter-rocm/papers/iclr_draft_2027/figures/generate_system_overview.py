#!/usr/bin/env python3
"""Generate the paper's contract-gated VLA system overview."""

from __future__ import annotations

from math import hypot
from pathlib import Path

from reportlab.graphics import renderPDF, renderPM
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String


WIDTH = 7.1 * 72
HEIGHT = 3.1 * 72
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def add_text(
    drawing: Drawing,
    x: float,
    y: float,
    lines: list[str],
    *,
    size: float = 7.2,
    leading: float = 10.0,
    color: str = "#202124",
    bold_first: bool = False,
) -> None:
    for index, line in enumerate(lines):
        drawing.add(
            String(
                x,
                y - index * leading,
                line,
                fontName=FONT_BOLD if bold_first and index == 0 else FONT,
                fontSize=size + (1.0 if bold_first and index == 0 else 0.0),
                fillColor=color,
            )
        )


def add_box(
    drawing: Drawing,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
    title: str,
    lines: list[str],
    size: float = 6.0,
    leading: float = 9.5,
) -> None:
    drawing.add(
        Rect(
            x,
            y,
            width,
            height,
            rx=4,
            ry=4,
            fillColor=fill,
            strokeColor=stroke,
            strokeWidth=1.2,
        )
    )
    add_text(
        drawing,
        x + 8,
        y + height - 15,
        [title, *lines],
        size=size,
        leading=leading,
        bold_first=True,
    )


def add_arrow(
    drawing: Drawing,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: str = "#4D5156",
    dashed: bool = False,
) -> None:
    length = hypot(x2 - x1, y2 - y1)
    if length == 0:
        raise ValueError("Arrow endpoints must be distinct")

    line = Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.4)
    if dashed:
        line.strokeDashArray = [4, 3]
    drawing.add(line)

    unit_x = (x2 - x1) / length
    unit_y = (y2 - y1) / length
    base_x = x2 - 6 * unit_x
    base_y = y2 - 6 * unit_y
    normal_x = -unit_y
    normal_y = unit_x
    drawing.add(
        Polygon(
            [
                x2,
                y2,
                base_x + 3.5 * normal_x,
                base_y + 3.5 * normal_y,
                base_x - 3.5 * normal_x,
                base_y - 3.5 * normal_y,
            ],
            fillColor=color,
            strokeColor=color,
        )
    )


def build_figure() -> Drawing:
    drawing = Drawing(WIDTH, HEIGHT)
    drawing.add(Rect(0, 0, WIDTH, HEIGHT, fillColor="#FFFFFF", strokeColor=None))
    add_text(
        drawing,
        10,
        HEIGHT - 16,
        ["Contract-gated PI0.5 adaptation and Radeon deployment"],
        size=10.5,
        bold_first=True,
    )
    add_text(
        drawing,
        10,
        HEIGHT - 31,
        ["Learned actions remain attributable to the VLA; deterministic code may decode, reject, or servo, but never complete the task."],
        size=6.8,
        color="#4D5156",
    )

    y = 91
    h = 82
    boxes = [
        (8, 78, "#EAF4FB", "#0072B2", "Observations", ["overhead/wrist RGB-D", "robot + seal/force", "language + phase/retry"]),
        (99, 83, "#FFF4E3", "#E69F00", "PI0.5 policy", ["LoRA action expert", "state + mode outputs", "receding-horizon replan"]),
        (195, 85, "#F3ECF8", "#CC79A7", "23-D action contract", ["base + dual-arm pose", "tool + mode outputs", "primitive progress"]),
        (293, 91, "#EAF7F2", "#009E73", "Execution boundary", ["normalize/transform", "servo interpolation", "hard limits + rejection"]),
        (397, 106, "#F2F2F2", "#4D5156", "Frozen evidence", ["action-fidelity gate", "paired development", "one-shot confirmation"]),
    ]
    for x, width, fill, stroke, title, lines in boxes:
        add_box(drawing, x, y, width, h, fill=fill, stroke=stroke, title=title, lines=lines)
    for index in range(len(boxes) - 1):
        x1 = boxes[index][0] + boxes[index][1]
        x2 = boxes[index + 1][0]
        add_arrow(drawing, x1 + 2, y + h / 2, x2 - 3, y + h / 2)

    add_box(
        drawing,
        8,
        14,
        247,
        55,
        fill="#FFF8E8",
        stroke="#D55E00",
        title="Verified improvement loop",
        lines=["failure telemetry -> correction candidate -> independent replay", "only verified successes become supervision; frozen gates decide promotion"],
        size=6.6,
    )
    add_box(
        drawing,
        269,
        14,
        234,
        55,
        fill="#EDF3F8",
        stroke="#0072B2",
        title="Radeon runtime evidence",
        lines=["persistent eager process; cold start separated from warm calls", "P50/P95/P99, peak VRAM, Wh/success, temperature, errors"],
        size=6.6,
    )
    add_arrow(drawing, 450, y - 3, 450, 72, color="#4D5156")
    add_arrow(drawing, 257, 42, 267, 42, color="#4D5156", dashed=True)
    return drawing


def main() -> None:
    output_dir = Path(__file__).resolve().parent
    drawing = build_figure()
    renderPDF.drawToFile(
        drawing,
        str(output_dir / "system_overview.pdf"),
        invariant=1,
    )
    try:
        renderPM.drawToFile(
            drawing,
            str(output_dir / "system_overview.png"),
            fmt="PNG",
            dpi=300,
        )
    except renderPM.RenderPMError as exc:
        print(f"Vector PDF created; optional PNG skipped: {exc}")


if __name__ == "__main__":
    main()
