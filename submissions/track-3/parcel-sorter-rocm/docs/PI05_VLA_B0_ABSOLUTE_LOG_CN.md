# PI0.5 B0 绝对动作 VLA 实验记录

## 声明边界

B0 是新的 `absolute_v1` 实验族，不继承 R11 adapter。纯 VLA 闭环要求每个策略步骤同时满足 `action_contract=pi05_absolute_v1`、`policy_authority=absolute_vla_action_candidate`、`expert_reference_used=false`、`selected_scale=1`、专家 fallback 为 0、急停为 0。确定性释放互锁允许保留，但 pregrasp、grasp approach、lift、transport 和 place 不允许使用专家运动动作。离线探针、训练损失和确定性专家成功均不计入 VLA 成功率。

## R11 因果结论

R11 的 5,871 帧训练标签中三个底盘 residual 通道全为零。严格开发闭环虽完成三种模式路由、抓取和抬升，但运输全部失败，结果为 0/3；其 authority 为专家参考加 VLA residual，不能计为纯 VLA。该证据停止了不能修复零标签的 R12 rank 和 R13 pooling 候选。

## B0 数据合同

输入为 80 维可观测状态。最后六维直接复制当前左、右末端位置 `state[24:27]` 和 `state[31:34]`，禁止由 action 目标反推。模式输入 `state[52:55]` 在所有阶段固定为零。输出为 23 维：19 维可执行绝对底盘/双臂动作、3 维模式 logits、1 维 primitive progress。

数据来自七条独立、物理验证成功的轨迹。顶部/原始侧吸分片重放两次，侧吸多样性分片一次，协同托架分片一次，共十个训练 episode。失败轨迹未加入行为克隆标签。

远端合并数据：`/workspace/parcel-sorter-opt-v1/outputs/pi05-b0-absolute-v1-merged`。

审计结果：

- 5,871 帧，模式 episode 分布为 top 4、side 4、cradle 2。
- 3,105 帧具有非零底盘命令监督。
- 5,871/5,871 帧模式输入隐藏；780/780 个 pregrasp 帧隐藏。
- 当前末端状态逐帧错配为 0；3,575 帧动作目标与当前末端位置有实质差异。
- 不安全量化归一化通道为 0；模式标签归一化前后 argmax 错配为 0。
- `expert_reference_used=false`，manifest 报告 action-derived state fields 为 0。

帧级模式交叉熵权重为 top `0.7608864697`、side `0.9200752233`、cradle `1.6697952218`。

## 架构与运行时

固定基座为 `lerobot/pi05_base` 的本地固定 revision `7de663972b7817d2c4cf2d84c821153dfea772e9`。训练使用 LoRA rank 16、alpha 32、冻结视觉编码器、observable state token、contextualized fused mode head、mode-head CE 权重 2、seed 11、30 步 action chunk、运行时首动作保持一拍。

Absolute Harness 不再将动作裁到专家动作附近。它只基于当前机器人状态、底盘速度上限、笛卡尔步长、力历史、深度风险和目标方向做安全投影。`scale<1` 会保留为安全降权证据，但不得计为纯 VLA。运输阶段禁止 deadline expert handoff。

闭环执行器已接通 pregrasp、grasp approach、lift、transport 和 place 的绝对底盘与双臂动作。每次阶段切换在首次物理动作前强制查询策略，防止阶段开头先执行专家轨迹。release 仍由确定性安全互锁执行并单独披露。

## 真实冒烟

2026-07-28 完成一次真实 4.145B PI0.5 的单步训练、反向传播、LoRA 保存和磁盘重载。可训练参数为 1,752,579，显存约 9.17 GB；训练输出维度为 23，合同明确 `expert_independent_absolute_mobile_action_v1` 和 `expert_reference=forbidden`。

重载后的完整扩散探针输出有限的 19 维可执行动作，产生非零底盘和双臂运动，`selected_scale=1`、`expert_reference_used=false`、fallback=0。单步模型模式预测错误，只证明训练/保存/部署链可用，不构成能力证据。

## 正式 B0 训练

正式 12,000 步训练 PID 为 `744683`，输出目录为 `/root/pi05-runs/mobile-pi05-b0-absolute-state-token-mode-head-12000-v1`，日志为 `outputs/pi05-b0-absolute-train-v1.log`。每 3,000 步保存 checkpoint。

post-screen 等待 PID 为 `747811`。训练正常结束后，它会用固定六观察、每观察三个共同随机种子检查 3k/6k/9k/12k checkpoint，并运行对应 `t=1` 诊断。离线筛选只用于开发候选选择，不计闭环成功率。

## 后续门禁

只有离线路由和动作门通过，才按不读取 held-out 和闭环结果的确定性规则选择候选。随后先运行 top、side、cradle 各一条严格开发闭环，要求完整抓取、运输、放置成功、全程 scale 1、专家引用和 fallback 为 0、接触力违规为 0。通过后才进行 action chunk、腕部 RGB-D 和验证式失败回放消融；最终冻结 105 回合只允许执行一次确认性评测。

工程目标为至少 95/105。若论文要在单侧 exact-binomial、`alpha=0.05` 下支持真实成功概率大于 0.90，则需要至少 100/105，不能把点估计超过 90% 当成统计声明。

## 验证式自进化合同

新增 80-D/23-D absolute replay writer。每帧标签由实际通过 Harness 的 19 维动作，加同次 π0.5 输出的三维模式 logits 和 progress 组成；末端状态仍从当前观测读取。只有完整任务成功、正确 VLA 路由、目标到达、全程 scale 1、absolute authority、专家引用和 fallback 为 0、急停和力违规为 0、运输无 deadline handoff、且存在非零底盘监督时才允许 finalize。其他运行清空缓冲区，失败动作不成为 BC 标签。

残差 replay 的归因门同时收紧：80-D/14-D residual 数据不能通过伪造 `absolute_vla_action_candidate` 被改标为纯 VLA；它必须披露 hybrid expert reference，且永远不算 pure-VLA experience。

通过门禁的 pure-VLA 自主成功轨迹会生成独立 `PI05_ABSOLUTE_DATASET_MANIFEST.json`，可与原始七条成功示范按明确采样权重合并。新增采集开关只合并通过上述门禁的成功分片；失败、专家 fallback、安全降权和接触力违规轨迹保留为审计与恢复队列，不直接训练。相关无 GPU 回归共 87 项通过。
