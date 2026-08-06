# Parcel Sorter ROCm / ROCm 包裹分拣

## English

Parcel Sorter ROCm is a Genesis parcel-sorting workcell running on one AMD
Radeon GPU with ROCm. The review video shows eight successful scripted runs,
made by `ScriptedPickPlaceExpert + ClosedLoopSupervisor` from a ten-episode
screen. It is simulation footage, not a VLA success video.

The learned route is reported separately: raw VLA passed 0/42 offline action
checks, bounded hybrid variants passed 42/42, and strict pure VLA scored 0/3.
The checkpoint records a 7-episode / 4,557-frame training set whose original
payload is no longer available. A separate seven-episode successful-trajectory
dataset is supplied in the local delivery and is not attributed to that checkpoint.

## 中文

Parcel Sorter ROCm 是在单张 AMD Radeon GPU 上通过 ROCm 运行的 Genesis 包裹分拣工位。评审视频展示 10 个 episode 中筛选出的 8 个成功脚本运行，控制器为 `ScriptedPickPlaceExpert + ClosedLoopSupervisor`。这是仿真视频，不是 VLA 成功视频。

学习路线单独报告：原始 VLA 离线动作检查为 0/42，受限混合版本为 42/42，严格纯 VLA 为 0/3。checkpoint 记录的训练集为 7 episode / 4,557 帧，但原始 payload 已不可用。本地交付另带一套 7 episode 成功轨迹数据集，不把它归因到该 checkpoint。
