# 数据集卡 / Dataset Card

## 当前候选

当前 SmolVLA 训练候选是 Genesis 派生的本地 LeRobot 数据集，记录的远端路径为
`/workspace/parcel-sorter-opt-v1/outputs/mobile-primitive-dataset-v2`。审计通过：7 个独立
episode（`0` 至 `6`）、4,557 帧、30 fps、43 维状态、20 维动作（含
`primitive_progress`）和 24 个任务文本。策略输入为俯视 RGB 加
`observation.state`；特权 parcel 状态被排除。

| 字段 | 审计值 |
| --- | --- |
| Episodes / episode | 7（`0` 至 `6`） |
| Frames / 帧 | 4,557 |
| Rate / 频率 | 30 fps |
| State / 状态 | 43-D |
| Action / 动作 | 20-D（含 `primitive_progress`） |
| Task texts / 任务文本 | 24 |
| RGB/depth audit / RGB-深度审计 | 检查 65 帧，0 次不匹配 |

## 可用性与边界

本仓库只有审计、manifest 和记录的哈希；Parquet、MP4 以及 metadata 二进制 payload
不在本地 checkout。因此它**当前不是可完整上传的数据集**，也没有公开 Hugging Face
URL。不得用本地 9-episode 数据集替代。

相关记录为
`evidence/training/pash-primitive-dataset-v2-audit.json` 和
`evidence/training/pash-primitive-dataset-v2-manifest.json`。manifest 包含 7 个输出
Parquet 文件的 SHA-256 值；恢复文件后必须逐一匹配。

## 历史数据

96 episode / 11,753 帧的 ACT 数据是 ACT baseline 的**历史 legacy 数据**。它不是本次
SmolVLA 候选，不能与上述数量合并，也不能按本候选 manifest 上传。

## 预期用途

仅可在恢复并完成验证后，用于模拟环境中的 SmolVLA 复现。它不是纯 VLA 成功证据、真实
机器人数据，也不是面向公众的通用数据集声明。发布步骤见
[Hugging Face 恢复与上传指南](../data/HUGGINGFACE_UPLOAD_GUIDE_EN_CN.md)。
