# Project Description / 项目描述

## English

Parcel Sorter ROCm is a Physical AI parcel-picking and sorting pipeline for a
single AMD Radeon GPU. It combines Genesis rigid-body simulation, aligned
RGB-D observations, a PI0.5-style policy adapter, stage/mode action heads,
closed-loop action-contract checks, and explicit attribution/safety gates.

The V20 experiment is a preregistered mode-only calibration: the direct action
and progress components are frozen from the V18 checkpoint while only
`mode_head` and `mode_head_state_residual` are trained on six unique frames per
stage/mode cell. This isolates a routing specialization factor without
changing the frozen panel, seeds, thresholds, or safety protocol.

The engineering contribution is the fail-closed evidence ladder. A checkpoint
must pass data admission, static audit, routing, action fidelity, and
structural checks before any closed-loop run. Rollouts record source/session
identity, policy authority, expert/fallback counters, force telemetry, and
media hashes. This makes a negative result reproducible instead of silently
crediting a shield or expert.

The V20 strict campaign completed 3/3 episodes with 0/3 complete pure-VLA
successes. The dominant failures were scene stability before material actuation
for two top-suction cases and contact acquisition for the side-suction case.
No force violation or expert fallback occurred.

## 中文

Parcel Sorter ROCm 是面向单张 AMD Radeon GPU 的 Physical AI 包裹抓取与分拣流水线，
结合 Genesis 刚体仿真、对齐 RGB-D 观测、PI0.5 风格策略适配器、阶段/模式动作头、
动作契约检查以及明确的归因和安全门。

V20 是预注册的 mode-only 校准实验：冻结 V18 checkpoint 中的 direct action 与
progress 组件，只在每个阶段/抓取模式单元中用 6 帧不重复样本训练
`mode_head` 和 `mode_head_state_residual`，不改变冻结 panel、seeds、阈值和安全协议。

项目的工程创新是 fail-closed 证据阶梯。checkpoint 必须先通过数据接纳、静态审计、
路由、动作保真度和结构检查，才允许闭环；每个 rollout 记录 source/session identity、
策略 authority、expert/fallback 计数、force telemetry 和媒体哈希，避免把 shield 或
专家行为误计为 VLA。

V20 严格评测完成 3/3，但完整纯 VLA 成功为 0/3。主要失败是两个 top-suction 案例在
实体动作前 scene stability 失败，以及 side-suction 案例接触获取失败；force violation
和 expert fallback 均为 0。
