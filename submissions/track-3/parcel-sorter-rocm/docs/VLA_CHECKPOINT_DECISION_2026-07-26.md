# VLA Checkpoint Decision / VLA Checkpoint 决策

## 中文

### 结论

保留 10k SmolVLA 作为当前 VLA 候选。停止继续训练，因为 12k 和 14k 的离线损失虽更低，闭环表现却退化。以下结果全部来自单张 AMD Radeon `gfx1100` GPU 和 ROCm 7.2。

### 证据

- 10k SmolVLA：五种包裹各运行一个固定未见回合，总成功率为 1/5。`small_carton` 首次尝试即完成抓取与放置，用时 5.37 秒，峰值接触力 12.87 N。`medium_carton` 和 `flat_mailer` 停在 `approach`；两种圆柱包裹均被安全门终止。
- 12k SmolVLA：验证损失为 0.1189，低于 10k 的 0.1355，但在完全相同的五个回合上为 0/5。
- 14k SmolVLA：验证损失为 0.1179，但固定小纸箱回合失败，峰值力达到 40.45 N。
- 2k delta-XYZ ACT：固定小纸箱回合停在 `approach`，峰值力仅 0.057 N；平均推理 3.18 ms，P95 为 8.54 ms。它是快速且安全的诊断基线，但尚不能完成任务。
- 2k delta-XYZ SmolVLA：验证损失为 0.3758，固定小纸箱回合失败并触发 46.74 N。该分支按预设门禁在 2k 后终止，没有继续消耗到 4k/6k。

### 下一步

下一项实验不再增加训练步数，而是修正任务条件：按包裹类型平衡训练采样，并让 VLA 文本明确包含包裹类型和目标分拣箱。目标分拣位置已存在于 20 维状态中，因此该实验主要验证语言条件能否减少跨形状动作平均化。每个 checkpoint 先运行一个固定闭环安全门，失败即停止，避免用离线 loss 代替机器人能力证据。

### 证据边界

当前只证明 10k checkpoint 完成过一个未见闭环回合，不能宣称五类包裹普遍成功。1/5 和 0/5 均为方向筛选证据，不是最终统计结论。

### 条件化均衡数据集结果（停止）

2026-07-26 在同一张 AMD Radeon `gfx1100` GPU、ROCm 7.2 上完成了 23 条动态语言指令、135 个训练回合的均衡条件化 SmolVLA 训练（10,000 steps）。最终 checkpoint 在固定 `small_carton` 闭环回合中为 `0/1`：19.97 s 后仍停留在 `approach`，峰值接触力仅 0.06 N。6k checkpoint 曾触发 40.23 N 安全中止。条件化分支没有超过原始 10k 模型的已验证 `small_carton` 成功，因此停止；不会为该分支消耗五类包裹扩测预算。

## English

### Decision

Retain the 10k SmolVLA checkpoint as the current VLA candidate. Stop further training because lower offline loss at 12k and 14k did not improve closed-loop behavior. Every result below was produced on one AMD Radeon `gfx1100` GPU with ROCm 7.2.

### Evidence

- 10k SmolVLA: one fixed unseen episode for each of five parcel profiles produced 1/5 successes. `small_carton` completed pick and place on the first attempt in 5.37 s with 12.87 N peak contact force. `medium_carton` and `flat_mailer` stopped in `approach`; both cylinder profiles were stopped by the safety gate.
- 12k SmolVLA: validation loss was 0.1189 versus 0.1355 at 10k, but it scored 0/5 on the identical episodes.
- 14k SmolVLA: validation loss was 0.1179, but the fixed small-carton episode failed and reached 40.45 N.
- 2k delta-XYZ ACT: the fixed small-carton episode stopped in `approach`, with only 0.057 N peak force. Mean inference was 3.18 ms and P95 was 8.54 ms. This is a fast, safe diagnostic baseline, not a task-capable replacement.
- 2k delta-XYZ SmolVLA: validation loss was 0.3758. The fixed small-carton episode failed and reached 46.74 N. The branch was stopped at the predefined 2k gate instead of consuming the planned 4k/6k budget.

### Next Experiment

Do not add training steps next. Correct task conditioning by balancing samples across parcel profiles and making the VLA text explicitly contain parcel profile and destination bin. The numeric destination is already present in the 20-D state, so this experiment tests whether language conditioning reduces cross-shape action averaging. Run one fixed closed-loop safety gate per checkpoint and stop failed branches early rather than treating offline loss as robot-capability evidence.

### Evidence Boundary

The current result proves only that the 10k checkpoint completed one unseen closed-loop episode. It does not establish general success across five parcel classes. The 1/5 and 0/5 results are directional screening evidence, not final statistical claims.

### Conditioned Balanced Dataset Result (Stopped)

On 2026-07-26, a balanced task-conditioned SmolVLA was trained for 10,000 steps on 135 episodes with 23 dynamic language instructions, using one AMD Radeon `gfx1100` GPU and ROCm 7.2. Its final checkpoint scored `0/1` on the fixed `small_carton` closed-loop episode: it remained in `approach` after 19.97 s with only 0.06 N peak contact force. Its 6k checkpoint had previously reached the 40.23 N safety abort. This branch did not exceed the verified `small_carton` success of the original 10k model, so it is stopped and will not consume a five-profile evaluation budget.
