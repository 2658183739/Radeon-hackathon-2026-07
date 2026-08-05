# 项目说明

Parcel Sorter ROCm 是一个以仿真为先的具身智能参赛项目：在单张 AMD Radeon GPU 上，使用 Franka Panda 模型完成包裹分拣。运行环境为 Genesis 1.2.3、ROCm 7.2.1、PyTorch 2.9.1 ROCm 和 LeRobot 0.6.1。

**做了什么。** 系统在 Genesis 仿真中抓取随机包裹并将其送至指定左/右格口；记录确定性脚本专家 agent 的轨迹，构建本地审计的 primitive 数据集，并在明确安全和归因门下运行策略实验。

**方法。** 俯视 RGB 与 43 维非特权状态输入策略；启用 primitive progress 时采用 20 维动作合约。固定频率的物理/控制循环施加有限值、笛卡尔、工具指令、IK 和力检查。统一证据台账标注数据集审计、ROCm 日志、离线消融和媒体边界。

**创新点。** 项目的贡献不是主张纯 VLA 已通过，而是可审计地分离参考示范、离线动作合约分析和严格纯 VLA 评测，并从锁定的上游 Panda MJCF 通过结构化方式生成版本化工具适配器。

项目严格区分三条证据轨道：

- 确定性脚本专家 agent：10 条轨迹中 8 条成功。该 agent 读取仿真特权状态并遵循有限状态任务监督器；它仅用于证明示范来源，不是 VLA 结果。
- 离线策略消融：42 个 episode-stage 动作合约样本。原始 VLA 的动作包络通过数为 0/42；安全裁剪 VLA 和 Harness-Lite 均为 42/42。
- 严格纯 VLA 评测：0/3 成功。该轨道未通过，不得表述为成功的 VLA 结果。

经审计的 primitive 数据集包含 7 个独立 episode 和 4,557 帧，包含 RGB、43 维非特权状态，以及带 primitive progress 的 20 维动作合约。本地证据包括数据集审计、训练日志、消融 JSON 和 PNG 曲线，具体路径见 `docs/TRAINING_EVIDENCE.md`。

评审链接：[PR #119（Open，base 为 `main`）](https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/119)；[仓库演示视频](https://github.com/2658183739/Radeon-hackathon-2026-07/blob/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4)；[raw MP4](https://raw.githubusercontent.com/2658183739/Radeon-hackathon-2026-07/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4)。该视频仅展示确定性脚本专家 agent 的仿真结果，不改变严格纯 VLA 0/3 的结果。

本仓库不主张 Sim-to-Real 迁移、真实机器人视频、TensorBoard 导出或公开数据集托管。证据边界见 `docs/SIM_TO_REAL_STATUS.md`。未主张上传 Bilibili。
