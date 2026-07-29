# PI0.5 VLA 实时研究状态（2026-07-28）

## 结论边界

本文只记录真实 PI0.5 训练、路由筛选和后续闭环入口。训练损失、离线路由探针、确定性专家结果以及接口测试都不计作 VLA 闭环成功率。截至本次快照，项目尚无证据支持 90% 以上完整抓取、运输和放置成功率。

## R9 最终结果

R9 已真实完成 12,000/12,000 步，最终 adapter SHA-256 为 `7f7875e702e16f036ea45f14de903114cc56f0b9612f48df487249d1d0b4723c`。训练 loss 中位数为 0.070，flow loss 中位数为 0.064；这些数字只证明优化完成。

3k、6k、9k 和 12k 四个 checkpoint 均未通过冻结的六观察路由门。12k 为 3/6：顶部吸附 2/2，侧面吸附 1/2，协同托架 0/2。因此 R9 没有进入严格闭环，不能报告 VLA 成功率提升。

## R10 最终结果

R10 使用同一 PI0.5 base、rank 16/alpha 32、12,000 步和同一数据，只把离散抓取模式从 flow action 通道改为 contextualized fused mode head。状态 token 保持关闭，因此这是相对 R9 的单因素架构消融。

R10 已完成 12,000/12,000 步。最终 adapter SHA-256 为 `ed14d1eb776ffaae71b80467f2ce9a32d3e33eb4bd78688ad91ecfeebe8cd390`，训练契约 SHA-256 为 `02997196a20e0e03ec15063ac5c5c6d74a73f09a296d17a647fc1563ccefce59`。早期训练 batch 出现过较高 mode-head accuracy 和正 margin，但冻结的 3k、6k、9k、12k 六观察筛选均只有 2/6：顶部吸附 2/2，侧面吸附 0/2，协同托架 0/2。四个 checkpoint 都稳定塌缩到顶部吸附，因此 R10 未进入闭环。

## R11 运行状态

R10 四个 checkpoint 全部失败后，顺序门于 2026-07-28 07:34 启动 R11。R11 保持相同 PI0.5 base、数据、seed、rank 16/alpha 32、类别平衡 fused mode head、12,000 步和冻结视觉编码器，唯一新增训练因素是 `parcel-pi05-state-token-v1`：物体形状、尺寸、质量等可观测状态经可学习投影注入 PI0.5 prefix。GPU 训练 PID 为 `700669`，post-screen PID 为 `700457`；R12 只在 R11 四个检查点全部失败后启动。R11 尚无能力结论。

R11 3k checkpoint 已通过无 GPU 静态审计：adapter SHA-256 为 `c18784fc0ea8e5ee82d463a2a599a5fa1e353dc65a110f0113415e4ba8b4a27c`，rank 16/alpha 32、80/14-D、state token v1、mode head v2、类别权重、归一化和训练契约均一致。该结果只证明 checkpoint 完整；冻结路由筛选仍等待 R11 全部训练结束。

## R13 预注册与等待门

R13 是相对 R11 的单因素 VLA 架构消融：只将模式头池化从 `masked_mean` 改为 `last_language_token`，其余 base、数据、seed、rank 16/alpha 32、state token、类别权重和训练步数全部冻结。协议为 `parcel-pi05-last-language-token-mode-head-v3`，已绑定训练、推理、契约、checkpoint 审计与遥测；远端 48 项回归通过。等待门 PID 为 `715036`，不占用 GPU；只有 R11 与 R12 四个 checkpoint 均未达到 6/6 时才允许启动 R13。

## Held-out 初始观察

为防止模型从物体位置猜抓取模式，冻结面板新增工作区位置区组：三种模式各自都覆盖 `-0.68/-0.45/-0.22/0.00 m` 四个 pedestal X 位置。采集格式只允许 RGB、metric depth、隐藏模式通道为零的 80-D pregrasp 状态和无模式词任务文本，禁止 action、recovery 和 outcome。采集等待 PID 为 `721367`，将在 R11/R12/R13 GPU 链全部释放后生成 12 个初始观察；它不会自动探测 checkpoint，也不能进入训练。

## 编排故障与修复

训练脚本原先将契约从 staging 目录复制到输出目录后直接执行 `rmdir`，遗留的源契约导致 `Directory not empty`。外层 Bash 因 `set -e` 退出，但 GPU Python 继续运行，因此训练未丢失，自动 postscreen 链却中断。

修复后使用原子 `mv` 搬移契约，再删除已空的 staging 目录。正在运行的 R10 未被停止；新的 postscreen 等待真实训练 PID。R10 到 R11、R11 到 R12 的顺序门已重新挂接，等待阶段不占用 GPU。任何上游 checkpoint 达到 6/6 时，链条都会停止新增训练并要求先做严格零回退闭环。

## 评测归因

运行时遥测现在区分 `hybrid_expert_reference_plus_vla_residual` 与 `absolute_vla_action_candidate`，并独立记录 `expert_reference_used` 和 `fallback_to_expert`。论文表格必须分别报告专家参考动作参与和专家回退，不能把 hybrid residual 结果写成纯绝对动作 VLA，也不能把确定性专家结果计入 VLA 成绩。

冻结晋级器现强制逐回合读取上述归因。系统级 hybrid 结果可以按原样报告，但纯 VLA 声明要求 105/105 回合全部为 absolute VLA、专家参考 0、专家回退 0、实质 residual 105/105、安全不退化，并达到至少 100/105 成功的单侧 exact-binomial 门。未知 authority 或仅部分回合有 residual 均 fail closed。

## 尚未满足的条件

目前没有任何 PI0.5 checkpoint 达到 90%，也尚未产生真实冻结 105 回合 VLA 成绩。项目已有的托架成功示范属于离线专家训练数据，不能计作 VLA 成绩。论文结果段必须等待 R11 或后续候选依次通过训练分布路由门、严格零回退开发闭环、冻结 held-out 路由和真实 105 回合评测后再定稿。

## 腕部 RGB-D 数据链准备

已为后续 R14 多视角消融补齐左腕 RGB、metric depth 和可视化 depth-RGB 的 opt-in 数据合同。仿真评测会根据左手末端实时位姿更新腕部相机，并在启用 `--wrist-rgbd` 时同时向 PI0.5 控制器、专家数据 writer 和验证式自主 replay writer 传入腕部观察；未启用该参数时，现有 overhead-only 路径、R11/R12/R13 契约和输入特征保持不变。

该改动已通过本地与 Radeon 隔离目录的 Python 编译、CLI 解析和 11 项数据合同/自进化归因测试，随后原子同步到实际远端仓库，远端真实环境的 11 项回归再次通过。它只证明数据链可用，不证明腕部视角改善了 VLA，也不会改变正在运行的 R11。2026-07-28 08:42 的最近观测约为 `7501/12000`；训练仍在运行，尚无新的路由或闭环成绩。

R14 视觉契约随后升级为 fail-closed：采集 summary、残差数据 manifest、不可变训练契约、checkpoint `input_features` 和运行时控制器必须报告同一组 policy-facing 视觉键。R11/R12/R13 固定为 overhead RGB-D 两键；R14 固定为 overhead RGB-D 加左腕 RGB-D 四键，缺失、只写入部分腕部通道或 checkpoint/data 不一致均拒绝。旧 R11 契约按其预注册的固定 overhead RGB-D 语义兼容读取，真实 3k checkpoint 复审仍通过。隔离环境共 27 项回归、Bash 语法和采集 CLI 通过，同步后的远端核心回归再次通过。08:54 的最近 R11 观测约为 `8733/12000`，仍无能力结论。

R14 训练前还必须通过 `pi05-wrist-single-factor-pairing-audit-v1`：overhead 对照和 wrist treatment 的成功 episode 顺序、物理参数、任务文本、帧索引、阶段、80-D 状态与 14-D 动作标签必须逐帧配对，默认数值容差为 `1e-6`。任何轨迹或监督漂移都会拒绝 R14，防止把重新采集造成的变化误归因于腕部视角。审计脚本的 3 项隔离回归已通过；尚无真实 wrist 数据，因此还没有配对结果。

R11 9k checkpoint 已通过无 GPU 静态审计，adapter SHA-256 为 `dc61d349a08e53ec8373ce58af451c396f5b68f57633c6f61b5fd9b1aa4cb2ad`，视觉输入仍为预注册 overhead RGB-D 两键，证据为 `evidence/pi05_vla/pi05-r11-step9000-static-audit.json`。该结果不代表路由或闭环能力。

## R11 训练完成与 post-screen 修复

R11 已于 2026-07-28 09:23 完成 `12000/12000` 步，训练日志包含 `End of training`，四个预注册 checkpoint 均已写出。该事实只证明优化过程完成，尚不构成路由或闭环能力证据。

首次自动 post-screen 在 3k checkpoint 的首个完整扩散探针中暴露运行时缺陷：阶段化 action-chunk 遥测错误引用仅存在于构造函数局部作用域的 `config`，触发 `NameError`。训练没有被停止或损坏，但原 post-screen 与后续 R12/R13 顺序门因 fail-closed 退出。现已将 chunk horizon 解析集中为控制器实例方法，统一读取 checkpoint 自身的 `self._config.chunk_size`；隔离目录和实际 Radeon 仓库的 27 项相关回归均通过。

修复后的 R11 9k overhead-only 兼容烟测完成了真实 PI0.5 加载和完整扩散推理：输出有限、19-D Harness 候选、专家 fallback 为 0，视觉指纹仍严格为 overhead RGB-D 两键；对应纯噪声端点诊断也成功读取相同视觉合同。这两项只证明推理和视觉合同兼容，不是六观察路由成绩，更不是闭环成功率。新的四 checkpoint post-screen 正在 `outputs/pi05-r11-common-seed-eval-v3/` 运行，PID 为 `729358`；在四份冻结 screen 完成前，不启动 R12，也不声明 R11 能力。

## R11 最终能力结论

修复后的 post-screen 已完整结束。R11 的 3k、6k、9k、12k 四个 checkpoint 均在同一冻结六观察、三共同随机种子面板上达到 `6/6`，三种抓取模式各为 `2/2`；对应 `t=1` 诊断也均为 `6/6`。按照不接触 held-out、不读取闭环结果的确定性规则，四者并列时选择最早达到门槛的 3k checkpoint，选择工件为 `evidence/pi05_vla/pi05-r11-checkpoint-selection-v1.json`。

3k 候选随后运行三条真实严格开发闭环。结果为 `0/3`：顶部吸附、侧面吸附和协同托架均由 PI0.5 正确选中，三条均形成抓取并完成抬升，力违规为 0；但三条运输均未到达目标，各发生一次专家接管，因此 `vla_qualified=0/3`。运行 authority 明确为 `hybrid_expert_reference_plus_vla_residual`，不能计作纯 VLA。

失败归因不是训练步数不足。当前 5,871 帧训练集的 `base_residual_vx/vy/vyaw` 三个通道在 min/max/mean/std/q01/q99 上全部为零；闭环中 PI0.5 的底盘 residual 范数约为 `1e-9`，运输实际依赖专家参考动作。R11 因此冻结为“模式路由成功、真正 VLA 运输失败”的消融；R12/R13 不再启动。下一候选 B0 改为 80-D 无动作泄漏可观测状态到 23-D 绝对动作，要求 `absolute_vla_action_candidate`、`expert_reference_used=false` 和 fallback=0。

## B0 绝对动作训练与自动门禁

B0 使用 80-D 可观测状态到 23-D 输出：前 19 维是可执行的绝对底盘/双臂动作，随后为三类抓取模式 logits 和 primitive progress。它不读取专家动作作为控制参考；Harness 只从当前机器人状态执行速度、笛卡尔步长、力、深度和目标方向安全投影。正式配置为固定 PI0.5 base revision、LoRA rank 16/alpha 32、冻结视觉编码器、state token、contextualized mode head、12,000 步、每 3,000 步保存。训练 PID 为 `744683`，post-screen PID 为 `747811`。

3k checkpoint 已完整保存，并在修复门禁后通过静态审计：23-D absolute action、80-D state、quantile normalization、state token、mode head、LoRA 16/32、固定基座 revision 和训练合同一致。该 checkpoint 的静态 adapter SHA-256 为 `504b7f4ab616c8c8d52188e743854fc73ad8fa3a1322f7cefa1fef92b57bec14`。这仍不代表路由或闭环能力。

本轮在任何 B0 离线筛选结果产生前修复了两个 fail-closed 编排缺陷。第一，模式汇总器输出协议已是 `pi05-three-mode-hidden-input-screen-v2`，checkpoint 选择器却仍要求 v1；选择器现与汇总器使用同一 v2，并增加跨脚本一致性回归。第二，静态审计器仍将所有 PI0.5 checkpoint 写死为 14-D residual，导致正确的 23-D absolute checkpoint 被误报为 action shape/name mismatch；审计器现只接受已声明的 14-D residual 或 23-D absolute 两套动作名，并继续由不可变训练合同校验语义。相关本地与 Radeon 回归均通过。

自动开发接力 PID 为 `764146`。它只等待 post-screen 正常结束，然后读取固定的 3k/6k/9k/12k 六观察 screen，按预注册的“全部门槛中最早通过”规则选择 checkpoint，再运行 top/side/cradle 各一条纯绝对动作严格开发闭环。该接力不读取 held-out，不运行最终 105 回合，也不会把专家或 hybrid 结果计入纯 VLA。最后一次记录时训练仍在运行，尚无 B0 闭环成功率结论。

## B0 复核与 B1/B2 接力准备

2026-07-28 12:28 UTC 复核时，B0 仍在正常训练，进度为 `8147/12000`，约 `1.87 step/s`，显存约 `9.18 GB`；3k 和 6k checkpoint 已存在，9k/12k、离线筛选和纯 VLA 三模式闭环尚未发生。因此当前应表述为“B0 尚无闭环结果”，不能把尚未评测写成 0%，也不能用训练 loss 代替能力。

官方 OpenPI 主分支仍只公开 π0、π0-FAST 和 π0.5，没有可复现的 π0.6/π0.7 权重或训练配置。与此同时，Hugging Face 已公开与本项目 LeRobot 代码同格式的 `lerobot/pi05_droid`，固定 revision 为 `72824c0a93f00ce5bb8bedb7feb58953ba1da364`；官方说明 DROID checkpoint 面向 Franka 且在实践中具有较广泛的跨场景泛化。B1 因此被预注册为相对 B0 只替换初始化 checkpoint 的单因素实验，其余数据、23-D absolute action、rank 16、视觉输入、seed、训练步数和 first-action runtime 均保持一致。B0 严格开发门失败时，等待脚本会自动启动 B1 的训练、四 checkpoint 筛选和三模式纯 VLA 开发闭环；不会访问 held-out 或最终 105。

B2 的 action-expert 适配也已实现但尚未训练：`action_in_proj` 和 `action_out_proj` 从 LoRA target 中移出，改为完整训练并随 PEFT checkpoint 持久化，协议固定为 `parcel-pi05-full-action-io-projections-v1`。训练合同和静态审计会同时核对该协议、adapter metadata 与实际 tensor，防止保存/重载后退回随机或基础动作投影。B2 必须在 B0/B1 结果冻结后作为单因素实验启动；rank 32、腕部 RGB-D 和有序 chunk 继续分别作为 B3/B4/B5，不能合并后声称某一个因素有效。

B2 的真实 Radeon 基座 round-trip 随后通过：峰值显存 `9.14 GB`，`modules_to_save` 精确包含 `action_in_proj/action_out_proj/state_proj/mode_head`，重载前后 action chunk、joint/fused mode logits 和 state embedding 的最大绝对差异均为 `0.0`；静态审计 `0` 错误，adapter SHA-256 为 `5b36704d8f891d5b7473ed3554a8fb4bc6367489a5211751809be2322f23b33b`。该证据只允许声称 B2 架构可保存、可重载、合同一致，不是训练或闭环能力。B1 等待 PID 为 `765892`。12:39 UTC 时 B0 为 `9315/12000`，9k checkpoint 已生成，仍无闭环结论。
