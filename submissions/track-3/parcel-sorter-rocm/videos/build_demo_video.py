#!/usr/bin/env python3
"""Render the eight-success deterministic expert demonstration package.

Inputs remain in the supplied evidence locations. This script writes only to
the output directory passed on the command line and records source/output
decode facts in JSON so the media can be independently audited.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


SUCCESS_IDS = (0, 1, 2, 4, 6, 7, 8, 9)
FPS = 10
WIDTH, HEIGHT = 1920, 1080
SOURCE_ROOT = Path(
    "/workspace/persistence/parcel-sorter-opt-v1/deliveries/"
    "success-video-pack-20260805/expert"
)
TWO_VIEW_ROOT = Path(
    "/workspace/persistence/parcel-sorter-opt-v1/deliveries/"
    "expert-two-view-20260805"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str,
         typeface: ImageFont.FreeTypeFont, fill=(244, 247, 250), anchor="la") -> None:
    draw.text(xy, value, font=typeface, fill=fill, anchor=anchor,
              stroke_width=1, stroke_fill=(0, 0, 0))


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
            fill, radius: int = 12, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def decode_video(path: Path) -> tuple[list[Image.Image], dict]:
    container = av.open(str(path))
    stream = container.streams.video[0]
    rate = float(stream.average_rate or stream.guessed_rate or FPS)
    images: list[Image.Image] = []
    try:
        for frame in container.decode(video=0):
            images.append(frame.to_image().convert("RGB"))
    finally:
        container.close()
    if not images:
        raise RuntimeError(f"Source video has no decodable frames: {path}")
    nonblank = []
    for index in (0, len(images) // 2, len(images) - 1):
        extrema = images[index].getextrema()
        nonblank.append(any(channel[1] > 0 for channel in extrema))
    return images, {
        "path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path),
        "resolution": [stream.width, stream.height], "fps": rate,
        "frame_count_decoded": len(images), "sample_frames_nonblank": nonblank,
        "decode_complete": all(nonblank),
    }


def normalized_index(index: int, output_length: int, input_length: int) -> int:
    if input_length <= 1 or output_length <= 1:
        return 0
    return round(index * (input_length - 1) / (output_length - 1))


def fit(image: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    return ImageOps.contain(image, (x1 - x0, y1 - y0), Image.Resampling.LANCZOS)


def episode_canvas(overview: Image.Image, wrist: Image.Image | None, episode: int,
                   ordinal: int, destination: str, subtitle_cn: str,
                   subtitle_en: str, fonts: dict[str, ImageFont.FreeTypeFont]) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (13, 19, 25))
    draw = ImageDraw.Draw(canvas)
    # Header and footer form a stable information frame around the rendered view.
    draw.rectangle((0, 0, WIDTH, 86), fill=(20, 28, 36))
    draw.rectangle((0, 86, 10, 932), fill=(237, 28, 36))
    text(draw, (34, 30), "GENESIS PARCEL SORTER", fonts["header"])
    text(draw, (34, 62), "确定性专家参考演示 / Deterministic expert reference demo", fonts["small"], fill=(184, 205, 218))
    rounded(draw, (1570, 20, 1878, 66), (26, 81, 76), radius=8)
    text(draw, (1724, 43), "SUCCESS TRUE / 成功", fonts["badge"], anchor="mm")

    if wrist is None:
        view_box = (54, 112, 1064, 899)
        view = fit(overview, view_box)
        px = view_box[0] + (view_box[2] - view_box[0] - view.width) // 2
        py = view_box[1] + (view_box[3] - view_box[1] - view.height) // 2
        canvas.paste(view, (px, py))
        draw.rectangle(view_box, outline=(77, 100, 113), width=2)
        text(draw, (72, 136), "OVERVIEW / 总览", fonts["small"], fill=(246, 249, 250))
    else:
        left_box, right_box = (52, 112, 1012, 899), (1030, 112, 1518, 899)
        for image, box, label in ((overview, left_box, "OVERVIEW / 总览"), (wrist, right_box, "WRIST / 腕部视角")):
            view = fit(image, box)
            px = box[0] + (box[2] - box[0] - view.width) // 2
            py = box[1] + (box[3] - box[1] - view.height) // 2
            canvas.paste(view, (px, py))
            draw.rectangle(box, outline=(77, 100, 113), width=2)
            text(draw, (box[0] + 18, box[1] + 24), label, fonts["small"], fill=(246, 249, 250))

    panel = (1542, 112, 1878, 899)
    rounded(draw, panel, (22, 31, 40), radius=8, outline=(62, 83, 98))
    text(draw, (1570, 160), f"EPISODE {episode:02d}", fonts["episode"], fill=(245, 248, 250))
    text(draw, (1570, 204), f"{ordinal:02d} / 08 verified", fonts["small"], fill=(163, 203, 209))
    draw.line((1570, 238, 1848, 238), fill=(72, 94, 107), width=2)
    text(draw, (1570, 285), "RESULT", fonts["small"], fill=(154, 177, 190))
    text(draw, (1570, 327), "SUCCESS", fonts["status"], fill=(103, 220, 179))
    text(draw, (1570, 392), "DESTINATION", fonts["small"], fill=(154, 177, 190))
    text(draw, (1570, 430), destination.upper(), fonts["episode"], fill=(244, 247, 250))
    text(draw, (1570, 512), "AMD Radeon + ROCm", fonts["small"])
    text(draw, (1570, 550), "Genesis 1.2.3", fonts["small"])
    text(draw, (1570, 588), "Official Franka Panda", fonts["small"])
    text(draw, (1570, 692), "DEV SCREENING", fonts["small"], fill=(154, 177, 190))
    text(draw, (1570, 734), "8 / 10", fonts["status"], fill=(253, 201, 87))
    text(draw, (1570, 787), "专家演示，非实体设备", fonts["tiny"], fill=(180, 196, 205))
    text(draw, (1570, 816), "Simulation reference", fonts["tiny"], fill=(180, 196, 205))

    draw.rectangle((0, 932, WIDTH, HEIGHT), fill=(19, 28, 36))
    text(draw, (54, 974), subtitle_cn, fonts["subtitle"])
    text(draw, (54, 1025), subtitle_en, fonts["caption"], fill=(201, 215, 223))
    text(draw, (1874, 1032), "AMD ROCm", fonts["tiny"], fill=(151, 177, 191), anchor="ra")
    return canvas


def final_canvas(thumbs: list[Image.Image], fonts: dict[str, ImageFont.FreeTypeFont]) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (13, 19, 25))
    draw = ImageDraw.Draw(canvas)
    slots = [(60 + (i % 4) * 455, 65 + (i // 4) * 250) for i in range(8)]
    for index, (image, xy) in enumerate(zip(thumbs, slots)):
        thumb = ImageOps.fit(image, (420, 220), Image.Resampling.LANCZOS)
        canvas.paste(thumb, xy)
        draw.rectangle((xy[0], xy[1], xy[0] + 420, xy[1] + 220), outline=(83, 115, 128), width=2)
        rounded(draw, (xy[0] + 14, xy[1] + 14, xy[0] + 128, xy[1] + 48), (26, 81, 76), radius=6)
        text(draw, (xy[0] + 71, xy[1] + 31), f"EP {SUCCESS_IDS[index]:02d}", fonts["tiny"], anchor="mm")
    draw.rectangle((0, 605, WIDTH, HEIGHT), fill=(19, 28, 36))
    text(draw, (960, 678), "8 / 10 DEVELOPMENT SCREENING", fonts["final"], anchor="ma", fill=(103, 220, 179))
    text(draw, (960, 735), "八个成功的确定性专家参考回合", fonts["subtitle"], anchor="ma")
    text(draw, (960, 786), "AMD Radeon + ROCm | Genesis 1.2.3 | Official Franka Panda", fonts["caption"], anchor="ma", fill=(201, 215, 223))
    text(draw, (960, 843), "github.com/2658183739/Radeon-hackathon-2026-07", fonts["url"], anchor="ma", fill=(245, 248, 250))
    text(draw, (960, 892), "TEAM / ACCOUNT 2658183739", fonts["caption"], anchor="ma", fill=(237, 28, 36))
    return canvas


def write_mp4(frames: list[Image.Image], path: Path) -> None:
    output = av.open(str(path), mode="w")
    stream = output.add_stream("libx264", rate=FPS)
    stream.width, stream.height = WIDTH, HEIGHT
    stream.pix_fmt = "yuv420p"
    stream.options = {"crf": "22", "preset": "medium", "movflags": "+faststart"}
    try:
        for index, image in enumerate(frames):
            frame = av.VideoFrame.from_ndarray(np.asarray(image), format="rgb24")
            frame.pts = index
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
    finally:
        output.close()


def decode_output(path: Path) -> dict:
    container = av.open(str(path))
    stream = container.streams.video[0]
    count, samples = 0, []
    try:
        for frame in container.decode(video=0):
            if count in (0, 25, 50) or count % 100 == 0:
                image = frame.to_image().convert("RGB")
                extrema = image.getextrema()
                samples.append({"frame": count, "nonblank": any(high > 0 for _low, high in extrema)})
            count += 1
    finally:
        container.close()
    duration = count / FPS
    return {
        "path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path),
        "codec": stream.codec_context.name, "resolution": [stream.width, stream.height],
        "fps": float(stream.average_rate or stream.guessed_rate or FPS),
        "frame_count_decoded": count, "duration_seconds": duration,
        "sample_frames": samples, "decodable": count > 0 and all(s["nonblank"] for s in samples),
    }


def release_position(trace: list[dict], source_frames: int) -> int:
    if not trace:
        return max(0, source_frames - 25)
    release = next((row for row in trace if row.get("stage") == "release"), trace[-1])
    frames = [int(row.get("frame", index)) for index, row in enumerate(trace)]
    return round((int(release.get("frame", frames[-1])) - min(frames)) * (source_frames - 1) /
                 max(1, max(frames) - min(frames)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--font", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--two-view-root", type=Path)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    summary = json.loads(
        (args.source_root / "summary.json").read_text(encoding="utf-8")
    )
    records = {int(row["episode_index"]): row for row in summary["episodes"]}
    missing = [episode for episode in SUCCESS_IDS if not records.get(episode, {}).get("result", {}).get("success")]
    if missing:
        raise RuntimeError(f"Required successful episodes failed source validation: {missing}")

    fonts = {
        "header": font(args.font, 32), "small": font(args.font, 22), "badge": font(args.font, 22),
        "episode": font(args.font, 31), "status": font(args.font, 38), "tiny": font(args.font, 18),
        "subtitle": font(args.font, 34), "caption": font(args.font, 25), "final": font(args.font, 42),
        "url": font(args.font, 30),
    }
    decoded: dict[int, list[Image.Image]] = {}
    source_audit: list[dict] = []
    wrists: dict[int, list[Image.Image]] = {}
    for episode in SUCCESS_IDS:
        path = args.source_root / "videos" / f"episode_{episode:06d}.mp4"
        decoded[episode], audit = decode_video(path)
        audit.update({"episode_index": episode, "summary_success": True,
                      "terminal_stage": records[episode].get("terminal_stage")})
        source_audit.append(audit)
        if episode in (0, 7):
            wrist_path = (
                args.source_root
                / "videos"
                / f"episode_{episode:06d}-wrist.mp4"
            )
            if not wrist_path.exists() and args.two_view_root is not None:
                wrist_path = (
                    args.two_view_root
                    / f"episode-{episode:06d}"
                    / "expert"
                    / "videos"
                    / f"episode_{episode:06d}-wrist.mp4"
                )
            wrists[episode], wrist_audit = decode_video(wrist_path)
            wrist_audit.update({"episode_index": episode, "role": "synchronized_wrist"})
            source_audit.append(wrist_audit)

    subtitles = {
        0: ("机械臂完成抓取、运输与释放，包裹稳定进入目标箱。", "The arm grasps, transports, and releases the parcel into the target bin."),
        1: ("不同扰动下的成功回合：全程保持稳定接触与目标对齐。", "Successful under a different perturbation: stable contact and target alignment."),
        2: ("专家参考动作在仿真环境中完成端到端分拣。", "The expert reference action completes end-to-end sorting in simulation."),
        4: ("包裹从工作台提起后被平稳放入指定位置。", "The parcel is lifted from the work surface and placed smoothly at the destination."),
        6: ("固定种子下的开发筛选：该回合记录为成功。", "Development screening under a fixed seed records this episode as successful."),
        7: ("腕部视角同步显示末端执行器的抓取与释放过程。", "The synchronized wrist view shows the end-effector through grasp and release."),
        8: ("目标区域内完成释放，终止状态为 complete。", "Release completes inside the target area with terminal state complete."),
        9: ("第八个入选成功回合，为本次 8/10 筛选收尾。", "The eighth selected success closes this 8/10 development screening."),
    }
    frames: list[Image.Image] = []
    # Hook: episode 0 release begins within the first five seconds.
    hook_source = decoded[0]
    hook_release = release_position(records[0].get("trace", []), len(hook_source))
    hook_start = max(0, hook_release - 22)
    for i in range(50):
        source_i = min(len(hook_source) - 1, hook_start + i)
        wrist_i = normalized_index(source_i, len(hook_source), len(wrists[0]))
        frames.append(episode_canvas(hook_source[source_i], wrists[0][wrist_i], 0, 1,
                                     str(records[0].get("sample", {}).get("destination", "target")),
                                     "释放验证：包裹稳定落入目标箱。", "Release verified: the parcel settles in the target bin.", fonts))
    # Main sequence: 6 seconds per selected successful overview episode.
    for ordinal, episode in enumerate(SUCCESS_IDS, start=1):
        overview = decoded[episode]
        cn, en = subtitles[episode]
        destination = str(records[episode].get("sample", {}).get("destination", "target"))
        for i in range(60):
            source_i = normalized_index(i, 60, len(overview))
            wrist = None
            if episode in wrists:
                wrist = wrists[episode][normalized_index(source_i, len(overview), len(wrists[episode]))]
            frames.append(episode_canvas(overview[source_i], wrist, episode, ordinal, destination, cn, en, fonts))
    # Final card is held for six seconds to keep attribution and repository legible.
    thumbs = [decoded[episode][-1] for episode in SUCCESS_IDS]
    card = final_canvas(thumbs, fonts)
    frames.extend([card] * 60)

    video_path = out / "genesis_panda_8_success_reference_demo.mp4"
    write_mp4(frames, video_path)
    thumbnail = frames[25].resize((1280, 720), Image.Resampling.LANCZOS)
    thumbnail.save(out / "thumbnail_1280x720.png", optimize=True)
    gif_frames = [frame.resize((640, 360), Image.Resampling.LANCZOS).convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
                  for frame in frames[:50:2]]
    gif_frames[0].save(out / "hook_5_seconds.gif", save_all=True, append_images=gif_frames[1:],
                       duration=200, loop=0, optimize=True, disposal=2)
    output_audit = decode_output(video_path)
    metadata = {
        "title": "Genesis Panda deterministic expert/reference demo: 8 successful episodes",
        "required_episode_ids": list(SUCCESS_IDS), "source_validation_passed": True,
        "source_audit": source_audit, "output": output_audit,
        "gif": {"path": str(out / "hook_5_seconds.gif"), "bytes": (out / "hook_5_seconds.gif").stat().st_size,
                "duration_seconds": 5.0},
        "thumbnail": {"path": str(out / "thumbnail_1280x720.png"), "bytes": (out / "thumbnail_1280x720.png").stat().st_size,
                      "resolution": [1280, 720]},
        "checks": {"duration_under_180_seconds": output_audit["duration_seconds"] < 180,
                   "resolution_1920x1080": output_audit["resolution"] == [1920, 1080],
                   "output_decodable_nonblank": output_audit["decodable"],
                   "gif_at_most_8mb": (out / "hook_5_seconds.gif").stat().st_size <= 8 * 1024 * 1024},
        "attribution": "AMD Radeon + ROCm; Genesis 1.2.3; official Franka Panda; deterministic expert/reference demo; development screening 8/10",
        "final_card": "https://github.com/2658183739/Radeon-hackathon-2026-07 | TEAM / ACCOUNT 2658183739",
    }
    (out / "video_metadata_decode.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    if not all(metadata["checks"].values()):
        raise RuntimeError(f"Validation failed: {metadata['checks']}")
    print(json.dumps({"output": output_audit, "checks": metadata["checks"]}, indent=2))


if __name__ == "__main__":
    main()
