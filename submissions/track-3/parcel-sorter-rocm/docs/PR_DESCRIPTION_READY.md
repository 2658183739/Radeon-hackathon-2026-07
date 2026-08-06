# Recommended PR Title / 建议 PR 标题

`[Physical AI] 2658183739 - Parcel Sorter ROCm`

# PR Description / PR 文案

## Project / 项目

**English.** Parcel Sorter ROCm runs Genesis parcel pick-and-place on one AMD Radeon GPU through ROCm. It contains deterministic control, separate SmolVLA/PI0.5 research paths, and a bounded hybrid-VLA safety harness.

**中文。** Parcel Sorter ROCm 在单张 AMD Radeon GPU 上通过 ROCm 运行 Genesis 包裹抓取与分拣，包含确定性控制、独立的 SmolVLA/PI0.5 研究路径和受限的混合 VLA 安全框架。

## Included / 包含内容

- **English:** Source, pinned ROCm container, reproduction commands, bilingual README, 59-second overview/wrist-view demo, 2,800-step local SmolVLA log and curve, 7-episode / 4,557-frame audit, and offline ablation evidence.
- **中文：** 源码、锁定的 ROCm 容器、复现命令、双语 README、59 秒全景/腕部视角演示、2,800-step 本地 SmolVLA 日志与曲线、7 episode / 4,557 帧审计和离线消融证据。

- **English:** GPT-5.6 Luna development/orchestration documentation. Luna does not control the robot.
- **中文：** GPT-5.6 Luna 研发/编排文档。Luna 不控制机器人。

## Results / 结果

| Route / 路径 | Result / 结果 | Meaning / 含义 |
| --- | ---: | --- |
| `ScriptedPickPlaceExpert + ClosedLoopSupervisor` | 8/10 | Successful demo clips; privileged Genesis state; deterministic expert/reference only / 成功视频片段；仅确定性专家参考 |
| Raw VLA offline envelope / 原始 VLA 离线包络 | 0/42 | Failed frozen action-validity checks / 未通过冻结动作有效性检查 |
| Bounded hybrid VLA / 受限混合 VLA | 42/42 | Offline validity only / 仅离线有效性 |
| Strict pure VLA / 严格纯 VLA | 0/3 | Not passed / 未通过 |

**English.** The video is scripted-controller simulation evidence, not GPT-5.6 Luna robot control, pure VLA, real-robot footage, or Sim-to-Real evidence.

**中文。** 视频是脚本控制器仿真证据，不是 GPT-5.6 Luna 控制机器人、纯 VLA、真实机器人视频或 Sim-to-Real 证据。

## Links / 链接

- Repository demo: <https://github.com/2658183739/Radeon-hackathon-2026-07/blob/track3-parcel-sorter-final/submissions/track-3/parcel-sorter-rocm/videos/genesis_panda_8_success_reference_demo.mp4>
- PR #119: <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/119>
- Public Bilibili/YouTube upload: `pending`
- Submitter / 提交者: `2658183739`
