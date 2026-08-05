# Competition Project Description / 比赛项目说明

## English

### What we built

Parcel Sorter ROCm is a Physical AI system that observes a parcel-sorting
workspace with synchronized RGB-D cameras and robot state, predicts task-level
grasp/placement actions with a PI0.5-style vision-language-action policy, and
executes them on an AMD Radeon GPU through a Genesis simulation and the
LeRobot-compatible action interface. The same evidence contract is used for
training, offline action screening, closed-loop execution, safety logging, and
video capture.

### Method

The competition candidate starts from a fingerprinted V18 PI0.5 checkpoint.
Two complete, safe RGB-D expert trajectories are admitted as training data;
one pre-action scene-stability failure is retained only as failure telemetry
and contributes no behavior-cloning label. The V20 candidate uses a frozen
direct-action/progress function and calibrates only the learned grasp-mode and
tool-decision heads. This isolates the diagnosed V19c regression: its routing
was correct, but updating the direct-action head caused six frozen-panel
primitive-progress errors.

All candidates are evaluated fail-closed in this order:

1. checkpoint, processor, attribution, and action-contract audit;
2. the original 12-observation frozen panel with common random numbers;
3. strict pure-VLA 3-episode closed loop with all media recorded;
4. delivery construction, MP4 decode/content-fingerprint verification, archive
   hashing, and packaged verification.

The safety layer may reject unsafe commands and enforce declared actuator
limits, but it cannot replace a failed action with an expert action. A rollout
counts as pure VLA only when the learned policy supplies every task action,
there is no expert/reference/fallback use, the complete destination/release
predicate passes, and force violations remain zero.

### Innovation

- A hash-bound action and observation contract makes the competition result
  reproducible instead of relying on a visually persuasive but unverifiable
  demo.
- RGB-D and explicit grasp-mode/tool heads separate contact-rich routing from
  continuous motion prediction.
- Failure telemetry is immutable and cannot silently become a positive label.
- The delivery verifier re-decodes every MP4 and rejects byte-different files
  that contain the same frames, preventing duplicated “three-video” evidence.
- AMD ROCm training, inference, safety, and media evidence are bundled with
  the exact commands and hashes used to produce them.

### Claim boundary

The competition result is a strict 3-case delivery smoke test, not an
unbiased confirmation estimate. Expert demonstrations receive zero VLA credit.
Any paper-grade generalization, cross-profile coverage, endurance, or
sim-to-real claim requires its own frozen protocol and is not inferred from
the competition MVP.

## 中文

### 我们做了什么

Parcel Sorter ROCm 是一个 Physical AI 包裹分拣系统。系统使用同步 RGB-D
相机和机器人状态观察工作空间，通过 PI0.5 风格视觉-语言-动作策略预测抓取、
搬运、放置动作，并在 AMD Radeon GPU 上运行 Genesis 仿真和兼容 LeRobot 的动作
接口。训练、离线动作筛选、闭环执行、安全日志和视频采集都遵循同一份证据契约。

### 方法

比赛候选从具有完整指纹的 V18 PI0.5 checkpoint 开始。数据只接纳两条完整且安全
的 RGB-D 专家轨迹；一次发生在 pregrasp 前的场景稳定性失败只保留为失败遥测，
不产生任何行为克隆标签。V20 保留已经通过 V18 冻结动作 panel 的直接动作/进度
函数，只校准学习得到的抓取模式和工具决策头，从而隔离 V19c 的具体回归：V19c
路由正确，但更新直接动作头后造成了六个冻结 panel 的 primitive-progress 误差。

所有候选严格按以下顺序执行：checkpoint/处理器/归因/动作契约审计；原始 12 个
观测的冻结 panel 和公共随机数采样；严格纯 VLA 三回合闭环并记录全部媒体；最后
构建交付包、重新解码并校验 MP4 内容指纹、生成归档哈希和运行包内验证器。

安全层可以拒绝危险动作并执行预先声明的执行器限制，但不能用专家动作替换失败
动作。只有学习策略输出全部任务动作、没有 expert/reference/fallback、完整到达和
释放判定通过且力超限为零时，才计为纯 VLA。

### 创新点

- 哈希绑定观测/动作契约，使比赛结果可复现、可审计，而不是只展示无法核验的视频。
- RGB-D 与显式抓取模式/工具决策头将接触丰富的路由问题和连续运动预测分离。
- 失败遥测不可变，不能在训练中被悄悄改成正样本。
- 交付验证器重新解码每个 MP4，拒绝“字节不同但画面相同”的重复视频。
- AMD ROCm 训练、推理、安全和媒体证据连同精确命令及哈希一起交付。

### 结论边界

比赛结果是严格三案例交付 smoke test，不是无偏确认集估计。专家演示不计入 VLA
成功。论文级泛化、跨 profile 覆盖、长时耐久性和 sim-to-real 结论必须使用独立
冻结协议，不能从比赛 MVP 推断。
