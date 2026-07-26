# Controller Probe V5 Decision Record / 控制器探针 V5 决策记录

## Decision / 决策

Freeze one independent 80-group confirmation of `veto-static` before any new
physics result is observed. Keep the active runtime on static geometry, keep
V2 development and holdout closed, and defer VLA, larger learned rankers, and
online parallel probes.

在观察任何新物理结果前，先冻结一套 80 组的 `veto-static` 独立确认实验。
当前运行时继续使用静态几何；V2 development 与 holdout 保持关闭；VLA、更大
学习排序器和在线并行探针暂不启动。

## Evidence Used / 使用的证据

V2 showed that two capacity-matched 6,276-parameter static-feature MLPs
increased safety aborts on development. V3 showed that a conservative KNN
memory could not improve task or safety outcomes in train-only cross
validation. V4 found one narrow positive mechanism: pre-place dynamics can
veto unsafe execution without reordering eligible candidates, preserving
7/32 successes while reducing force aborts from 17/32 to 13/32 on train.

V2 的两套 6,276 参数静态特征 MLP 在 development 上增加了安全中止；V3 的
保守 KNN 记忆在 train-only 交叉验证中没有任务或安全净改善；V4 只找到一个
边界清晰的正向机制：放置前动态信息可用于否决危险执行，但不能主动重排合格
候选。它在 train 上保留 7/32 成功，并把力中止从 17/32 降到 13/32。

## Alternatives Rejected / 暂不采用的方案

- More MLP capacity: the failure was calibration and missing dynamics, not
  inference latency or parameter count.
- Threshold search on V2/V4 data: those outcomes have already influenced the
  chosen mechanism and cannot provide independent confirmation.
- Immediate VLA low-level control: current evidence and dataset size do not
  support replacing the deterministic safety controller.
- Cylinders in V5: the registered candidate generator is box-specific, so
  adding cylinders would confound planner capability with veto validity.
- Immediate runtime activation: V4 used offline counterfactual trajectories;
  no online scene-clone cost or synchronization evidence exists yet.

- 扩大 MLP：当前失败来自失准与动态信息缺失，不是延迟或参数量不足。
- 在 V2/V4 上继续扫阈值：这些结果已经影响机制选择，不能再承担独立确认职责。
- 直接让 VLA 控低层关节：当前数据量与闭环证据不足以替代确定性安全控制器。
- V5 混入圆柱：现有候选生成器仅支持箱体，会把规划器能力与否决器有效性混在一起。
- 立即启用运行时：V4 依赖离线反事实轨迹，尚无在线场景克隆成本和同步证据。

## Implementation Boundary / 实现边界

V5 adds an isolated all-rigid-box collection entry point rather than changing
the shared V2/V3 activation contract. The confirmation module consumes only
the causal pre-place trace prefix, reports paired statistics and perturbation
strata, and never changes the frozen V4 source files.

V5 通过独立的“全部刚性箱体”采集入口扩展总体，而不修改 V2/V3 共用激活契约。
确认模块只读取因果截断后的放置前轨迹，输出配对统计与扰动分层，也不改动 V4
冻结源文件。

## Verification / 验证

- Population selection: 80 groups, zero old-key overlap, no scene or outcome read.
- Collection dry run: 80 groups, maximum 480 full candidate rollouts.
- Protocol audit: `protocol_valid`, no errors.
- Test suite: 304 passed, 1 environment-dependent skip.
- Protocol SHA-256: `062e3ec9d0c4968b1593331ada5aa1aa737e4eadda869e173fe0116e3ab8101e`.

- 总体选择：80 组，与旧键零重叠，不构造场景、不读取结果。
- 采集预演：80 组，最多 480 条完整候选 rollout。
- 协议审计：`protocol_valid`，无错误。
- 测试：304 项通过，1 项按环境跳过。
- 协议 SHA-256：`062e3ec9d0c4968b1593331ada5aa1aa737e4eadda869e173fe0116e3ab8101e`。
