# Dataset Release Status / 数据集发布状态

**English.** The current candidate is exactly 7 episodes / 4,557 frames / 30 fps / 43-D state / 20-D action / 24 task texts. Its only recorded location is remote:
`/workspace/parcel-sorter-opt-v1/outputs/mobile-primitive-dataset-v2`.

**中文。** 当前候选严格为 7 episode / 4,557 帧 / 30 fps / 43-D state / 20-D action / 24 task texts；唯一记录位置为远端：`/workspace/parcel-sorter-opt-v1/outputs/mobile-primitive-dataset-v2`。

This checkout contains audit, manifest, and hashes only. It lacks the required
LeRobot v3 Parquet, MP4, and metadata binaries, so it is **not yet uploadable**.
Do not replace it with a 9-episode local dataset. The 96-episode / 11,753-frame
ACT corpus is legacy historical data, not current SmolVLA training evidence.

Sources: [`pash-primitive-dataset-v2-audit.json`](../evidence/training/pash-primitive-dataset-v2-audit.json) and [`pash-primitive-dataset-v2-manifest.json`](../evidence/training/pash-primitive-dataset-v2-manifest.json).

See [Hugging Face recovery and upload guide](HUGGINGFACE_UPLOAD_GUIDE_EN_CN.md) before making any publication claim.
