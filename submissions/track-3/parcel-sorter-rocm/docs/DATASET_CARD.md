# Dataset Card / 数据集卡

## Current Candidate / 当前候选

**English.** The current SmolVLA training candidate is a Genesis-derived local
LeRobot dataset at the recorded remote path
`/workspace/parcel-sorter-opt-v1/outputs/mobile-primitive-dataset-v2`. Its
audit passed with 7 independent episodes, 4,557 frames at 30 fps, 43-D state,
20-D action (including `primitive_progress`), and 24 task texts. Policy inputs
are overhead RGB plus state; privileged state is excluded.

**中文。** 当前 SmolVLA 训练候选是 Genesis 派生的本地 LeRobot 数据集，记录的远端路径为
`/workspace/parcel-sorter-opt-v1/outputs/mobile-primitive-dataset-v2`。审计通过：7 个独立
episode、4,557 帧、30 fps、43 维状态、20 维动作（含 `primitive_progress`）和 24 个任务文本。策略输入为俯视 RGB 加状态；特权状态被排除。

| Field / 字段 | Audited value / 审计值 |
| --- | --- |
| Episodes / episode | 7 (`0` through `6`) |
| Frames / 帧 | 4,557 |
| Rate / 频率 | 30 fps |
| State / 状态 | 43-D |
| Action / 动作 | 20-D |
| Task texts / 任务文本 | 24 |
| RGB/depth audit / RGB-深度审计 | 65 checked frames, 0 mismatches |

## Availability and Boundary / 可用性与边界

**English.** This repository contains only the audit, manifest, and recorded
hashes. The Parquet, MP4, and metadata payload are absent from this checkout;
therefore it is **not currently a complete uploadable dataset** and has no
public Hugging Face URL. Do not substitute a local 9-episode dataset.

**中文。** 本仓库只有审计、manifest 和记录的哈希；Parquet、MP4 和 metadata 二进制不在本地 checkout。因此它**当前不是可完整上传的数据集**，也没有公开 Hugging Face URL。不得用本地 9-episode 数据集替代。

The relevant records are `evidence/training/pash-primitive-dataset-v2-audit.json`
and `evidence/training/pash-primitive-dataset-v2-manifest.json`. The manifest
contains seven output-Parquet SHA-256 values, which must match recovered files.

## Legacy Data / 历史数据

**English.** The 96-episode / 11,753-frame ACT data is **legacy historical
data** for an ACT baseline. It is not this SmolVLA candidate, must not be
combined with these counts, and must not be uploaded under this candidate's
manifest.

**中文。** 96 episode / 11,753 帧 ACT 数据是 ACT baseline 的**历史 legacy 数据**。它不是本次 SmolVLA 候选，不能与上述数量合并，也不能按本候选 manifest 上传。

## Intended Use / 预期用途

Use only after recovery and verification for simulated SmolVLA reproduction.
It is not pure-VLA success evidence, real-robot data, or a general public
dataset claim. Release steps are in [the upload guide](../data/HUGGINGFACE_UPLOAD_GUIDE_EN_CN.md).
