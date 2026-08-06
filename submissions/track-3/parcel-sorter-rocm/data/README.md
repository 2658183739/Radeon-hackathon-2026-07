# Data / 数据

The submitted SmolVLA checkpoint records a training set with 7 episodes, 4,557
frames, 43-D state, 20-D action and 24 task texts. Its audit and manifest are
kept in `evidence/training/`; the original Parquet, video and metadata payload
is no longer present locally or on the Radeon workspace.

提交的 SmolVLA checkpoint 记录使用 7 个 episode、4,557 帧、43-D state、20-D
action 和 24 条 task text。审计与 manifest 保存在 `evidence/training/`；原始
Parquet、视频和 metadata payload 已不在本地或 Radeon 工作区。

The local final delivery includes a different, complete LeRobot v3 release:
7 successful episodes, 6,454 frames, 43-D state, 19-D action, and overhead plus
left-wrist RGB-D. It includes 53 dataset files whose SHA-256 hashes match the
Radeon source. It is supplied as an independent successful-trajectory dataset,
not as training evidence for the submitted checkpoint.

最终本地交付另带一套不同的完整 LeRobot v3 发布集：7 个成功 episode、6,454 帧、
43-D state、19-D action，以及 overhead 与左腕 RGB-D。数据集共 53 个文件，
SHA-256 与 Radeon 源文件逐项一致。它是独立成功轨迹数据集，不作为提交 checkpoint
的训练证据。
