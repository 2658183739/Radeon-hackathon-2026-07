#!/usr/bin/env python3
"""Render bounded training and offline-ablation evidence boards from audited JSON.

The figures intentionally report one recorded Radeon run (n=1), omit error
bars, and preserve the evidence boundary: offline envelope checks are not
closed-loop VLA task successes and are not Sim-to-Real results.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


W, H = 1920, 1080
BG = (13, 21, 29)
PANEL = (22, 34, 44)
PANEL_ALT = (27, 42, 54)
INK = (239, 245, 248)
MUTED = (171, 191, 202)
GRID = (69, 91, 104)
GREEN = (56, 190, 142)
RED = (237, 94, 96)
BLUE = (82, 166, 220)
GOLD = (244, 188, 74)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_font(font_path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path), size=size)


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
          font: ImageFont.FreeTypeFont, fill=INK, anchor="la") -> None:
    draw.text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=0)


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill=PANEL,
         border=GRID, radius=14) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=border, width=2)


def clip_text(draw: ImageDraw.ImageDraw, text_value: str,
              font: ImageFont.FreeTypeFont, max_width: int) -> str:
    if draw.textlength(text_value, font=font) <= max_width:
        return text_value
    suffix = "..."
    while text_value and draw.textlength(text_value + suffix, font=font) > max_width:
        text_value = text_value[:-1]
    return text_value + suffix


def header(canvas: Image.Image, draw: ImageDraw.ImageDraw, fonts: dict) -> None:
    draw.rectangle((0, 0, W, 112), fill=(17, 29, 38))
    draw.rectangle((0, 0, 12, 112), fill=RED)
    label(draw, (40, 42), "Training Evidence Board / 训练证据看板", fonts["title"])
    label(draw, (40, 83), "Single Radeon run | n=1 | static artifact, not TensorBoard", fonts["sub"], MUTED)
    card(draw, (1454, 28, 1878, 82), fill=(41, 72, 76), border=(77, 133, 127), radius=9)
    label(draw, (1666, 55), "SIMULATION EVIDENCE / 仿真证据", fonts["badge"], anchor="mm")


def metric_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], value: str,
                en: str, cn: str, color, fonts: dict) -> None:
    card(draw, box, fill=PANEL_ALT)
    x0, y0, _x1, _y1 = box
    label(draw, (x0 + 26, y0 + 46), value, fonts["metric"], color)
    label(draw, (x0 + 26, y0 + 89), en, fonts["small"], INK)
    label(draw, (x0 + 26, y0 + 120), cn, fonts["tiny"], MUTED)


def training_board(root: Path, out: Path, fonts: dict) -> None:
    evidence = load_json(root / "evidence/training/pash-primitive-smolvla-rocm-2800step-v1.json")
    dataset = load_json(root / "evidence/training/pash-primitive-dataset-v2-audit.json")
    ablation = load_json(root / "evidence/training/pash-primitive-smolvla-2800step-offline-ablation-v1.json")
    results = load_json(root / "submission_materials/RESULTS.json")
    training = evidence["training"]
    assert evidence["runtime"]["gpu_count"] == 1 and training["steps"] == 2800
    assert dataset["episodes"] == 7 and dataset["frames"] == 4557
    assert ablation["offline_ablation"]["raw_vla"]["envelope_pass_count"] == 0
    assert results["pure_vla_successes"] == 0 and results["trials"] == 3

    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    header(canvas, draw, fonts)

    # Existing loss curve is included verbatim; this board adds only labeled context.
    curve_box = (38, 144, 1160, 654)
    card(draw, curve_box)
    label(draw, (70, 184), "A  Recorded training loss / 已记录训练损失", fonts["section"])
    label(draw, (70, 219), "2,800 updates; loss 2.164 -> 0.056. No uncertainty band: one run (n=1).", fonts["small"], MUTED)
    curve = Image.open(root / "docs/assets/pash-primitive-smolvla-2800step-training-curve-v1.png").convert("RGB")
    curve = ImageOps.contain(curve, (1060, 372), Image.Resampling.LANCZOS)
    canvas.paste(curve, (70 + (1060 - curve.width) // 2, 264 + (372 - curve.height) // 2))

    metric_card(draw, (1190, 144, 1518, 300), "2,800", "logged updates", "已记录更新步数", BLUE, fonts)
    metric_card(draw, (1550, 144, 1878, 300), f"{training['mean_steps_per_second']:.2f}", "steps / second", "步 / 秒", GREEN, fonts)
    metric_card(draw, (1190, 322, 1518, 478), f"{training['reported_peak_memory_gb']:.2f} GB", "reported peak memory", "报告峰值显存", GOLD, fonts)
    metric_card(draw, (1550, 322, 1878, 478), "7 / 4,557", "episodes / frames", "回合 / 帧数", BLUE, fonts)
    card(draw, (1190, 500, 1878, 654), fill=(42, 44, 56), border=(115, 93, 98))
    label(draw, (1218, 540), "STRICT PURE VLA / 严格纯 VLA", fonts["small"], MUTED)
    label(draw, (1218, 587), "0 / 3  NOT PASSED", fonts["metric"], RED)
    label(draw, (1218, 625), "closed-loop simulation; no VLA task-success claim", fonts["tiny"], INK)

    offline = ablation["offline_ablation"]
    card(draw, (38, 682, 1878, 930))
    label(draw, (70, 723), "B  Offline action-envelope check / 离线动作包络检查", fonts["section"])
    label(draw, (70, 757), "42 episode-stage samples from 7 episodes; this is not a closed-loop task-success evaluation.", fonts["small"], MUTED)
    rows = [
        ("Raw VLA / 原始 VLA", offline["raw_vla"], RED),
        ("Safety-clipped VLA / 安全裁剪 VLA", offline["safety_clipped_vla"], GREEN),
        ("Harness-Lite / 轻量安全框架", offline["harness_lite"], BLUE),
    ]
    for index, (name, row, color) in enumerate(rows):
        x0 = 70 + index * 595
        card(draw, (x0, 790, x0 + 550, 900), fill=PANEL_ALT, border=color, radius=10)
        label(draw, (x0 + 22, 826), name, fonts["small"])
        label(draw, (x0 + 22, 873), f"{row['envelope_pass_count']} / 42", fonts["metric"], color)
        label(draw, (x0 + 250, 865), f"mean MAE {row['mean_mae']:.5f}", fonts["tiny"], MUTED)

    draw.rectangle((0, 956, W, H), fill=(17, 29, 38))
    label(draw, (40, 998), "Boundary / 边界: single recorded run; no error bars; no TensorBoard, Sim-to-Real, or pure-VLA success claim.", fonts["small"], INK)
    label(draw, (40, 1036), "Sources: pash-primitive-smolvla-rocm-2800step-v1.json | dataset-v2-audit.json | offline-ablation-v1.json | RESULTS.json", fonts["tiny"], MUTED)
    canvas.save(out / "training_evidence_board_1920x1080.png", optimize=True)


def ablation_board(root: Path, out: Path, fonts: dict) -> None:
    evidence = load_json(root / "evidence/training/pash-primitive-smolvla-2800step-offline-ablation-v1.json")
    results = load_json(root / "submission_materials/RESULTS.json")
    offline = evidence["offline_ablation"]
    treatments = [
        ("Expert executor\n专家执行器", offline["expert_executor"], GOLD),
        ("Raw VLA\n原始 VLA", offline["raw_vla"], RED),
        ("Safety-clipped VLA\n安全裁剪 VLA", offline["safety_clipped_vla"], GREEN),
        ("Harness-Lite\n轻量安全框架", offline["harness_lite"], BLUE),
    ]
    assert results["pure_vla_successes"] == 0 and results["trials"] == 3
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, W, 112), fill=(17, 29, 38))
    draw.rectangle((0, 0, 12, 112), fill=BLUE)
    label(draw, (40, 42), "Offline Action-Envelope Comparison / 离线动作包络对比", fonts["title"])
    label(draw, (40, 83), "42 episode-stage samples from 7 episodes | offline only | no error bars", fonts["sub"], MUTED)

    chart = (84, 174, 1204, 824)
    card(draw, chart)
    label(draw, (120, 220), "Envelope passes / 包络通过数", fonts["section"])
    x_axis0, x_axis1, y_base, y_top = 164, 1128, 708, 300
    for tick in (0, 10, 20, 30, 42):
        y = y_base - (y_base - y_top) * tick / 42
        draw.line((x_axis0, y, x_axis1, y), fill=GRID, width=1)
        label(draw, (144, y), str(tick), fonts["tiny"], MUTED, anchor="ra")
    bar_width = 150
    for index, (name, row, color) in enumerate(treatments):
        x = 230 + index * 220
        count = row["envelope_pass_count"]
        bar_top = y_base - (y_base - y_top) * count / 42
        draw.rounded_rectangle((x, bar_top, x + bar_width, y_base), radius=10, fill=color)
        label(draw, (x + bar_width // 2, bar_top - 24), f"{count}/42", fonts["metric"], color, anchor="ma")
        for line_index, line in enumerate(name.splitlines()):
            label(draw, (x + bar_width // 2, 756 + line_index * 28), line, fonts["small"], INK, anchor="ma")

    card(draw, (1240, 174, 1836, 824), fill=PANEL)
    label(draw, (1272, 220), "Recorded mean errors / 记录均值误差", fonts["section"])
    label(draw, (1272, 255), "No intervals: one offline measurement set.", fonts["tiny"], MUTED)
    y = 318
    for name, row, color in treatments:
        short = name.splitlines()[0]
        label(draw, (1272, y), clip_text(draw, short, fonts["small"], 330), fonts["small"], color)
        label(draw, (1272, y + 33), f"MAE {row['mean_mae']:.5f}     MSE {row['mean_mse']:.6f}", fonts["tiny"], INK)
        label(draw, (1730, y + 33), f"{row['envelope_pass_count']}/42", fonts["small"], color, anchor="ra")
        draw.line((1272, y + 66, 1804, y + 66), fill=GRID, width=1)
        y += 112
    card(draw, (84, 856, 1836, 1006), fill=(42, 44, 56), border=(115, 93, 98))
    label(draw, (116, 900), "Result boundary / 结果边界", fonts["section"], RED)
    label(draw, (116, 942), "Raw VLA: 0/42; clipped VLA and Harness-Lite: 42/42 offline envelope passes. Strict pure VLA: 0/3, not passed.", fonts["small"], INK)
    label(draw, (116, 978), "离线安全包络检查不等于闭环任务成功；不主张 Sim-to-Real 或纯 VLA 成功。", fonts["small"], MUTED)
    canvas.save(out / "ablation_comparison.png", optimize=True)


def verify(path: Path, expected_size: tuple[int, int] = (W, H)) -> dict:
    image = Image.open(path).convert("RGB")
    extrema = image.getextrema()
    nonempty = any(high > 0 for _low, high in extrema)
    if image.size != expected_size or not nonempty:
        raise RuntimeError(f"invalid image {path}: size={image.size}, nonempty={nonempty}")
    return {"path": str(path), "size": image.size, "nonempty": nonempty, "bytes": path.stat().st_size}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or args.repo_root / "docs/assets"
    out.mkdir(parents=True, exist_ok=True)
    fonts = {
        "title": get_font(args.font, 38), "sub": get_font(args.font, 24),
        "badge": get_font(args.font, 19), "section": get_font(args.font, 28),
        "metric": get_font(args.font, 40), "small": get_font(args.font, 23), "tiny": get_font(args.font, 18),
    }
    training_board(args.repo_root, out, fonts)
    ablation_board(args.repo_root, out, fonts)
    print(json.dumps([verify(out / "training_evidence_board_1920x1080.png"), verify(out / "ablation_comparison.png")]))


if __name__ == "__main__":
    main()
