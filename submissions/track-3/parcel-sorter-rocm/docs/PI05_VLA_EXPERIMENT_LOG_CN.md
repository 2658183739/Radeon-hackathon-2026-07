# π0.5 VLA 实验日志

最后更新：2026-07-28

## 声明边界

本项目的学习策略主体是 π0.5。冻结评测只统计由 π0.5 实际完成抓取模式选择、接触残差预测、任务进度判断和闭环动作执行的回合。几何、IK、碰撞、力限和误释放保护属于 Harness 安全投影，不计为学习策略贡献。解析恢复控制器只用于离线生成并验证示范；其成功率不得作为 VLA 成功率。冻结 105 回合的最低工程门槛为至少 95/105 成功、专家回退为 0、VLA 合格回合为 105/105，且接触力违规不得高于基线；论文若声明总体成功概率超过 90%，还必须达到至少 100/105 并通过单侧精确二项检验。

## R0：旧 π0.5 种子模型

旧模型来自极短 ROCm 链路探针，并非有效微调。三模式严格筛选为 0/5；模型始终输出 `top_suction`，接触残差约为 `1e-8 m`，等同零动作。因此旧的单回合成功不能证明 π0.5 学会抓取。证据见 `evidence/pi05_vla/pi05-strict-three-mode-screen-v1-audit.json` 和对应 collection 文件。

## 控制合同修正

π0.5 输入为顶部 RGB-D 和 80 维可观测状态，输出为 14 维受约束动作：3 维底盘残差、左右接触点各 3 维残差、3 个抓取模式 logit、吸盘命令和任务进度。pregrasp、grasp approach、lift 和 transport 的机械臂权限分别限制在 20、10、5 和 10 mm。姿态、IK、碰撞和力限仍由 Harness 掌握。

早期实现只把 π0.5 的模式输出用于正确性判定，但实际执行分支仍由命令行标签选择。该实现不满足 VLA 路由要求。现已在任何模式专用 IK 和接触目标生成之前进行一次无模式提示的 π0.5 推理，并由其输出直接选择顶部吸附、侧面吸附或协同托架分支。`--grasp-mode` 在严格评测中仅作为隐藏真值，日志分别保存 expected、selected 和 executed 模式。

为降低扩散动作采样带来的单次模式抖动，路由阶段默认对同一 RGB-D 观察进行 3 次 π0.5 采样，先以模式票数、再以平均 logit 破平局。该共识过程不读取隐藏标签，不调用专家路由，并记录 vote counts、mean logits 和 consensus fraction。论文中将单样本路由与三样本共识作为独立消融，报告额外推理延迟与成功率变化。

## R1：验证成功恢复数据上的 1,000 步 LoRA

R1 使用 π0.5 base、LoRA rank 16、alpha 32、冻结视觉编码器、bfloat16、batch size 1 和 1,000 步训练。训练数据包含 3 条完整验证成功的恢复 episode，共 1,818 帧，其中 1,458 帧具有非零接触残差。数据覆盖两个顶部吸附 episode 和一个侧吸 episode，不包含托架成功示范。checkpoint 位于远端 `/root/pi05-runs/mobile-pi05-recovery-1000-v2/checkpoints/001000/pretrained_model`，adapter SHA-256 为 `208c62772b7f8d7eccb912088a1c0ef3de9153d1fc2f2f8ec501f9c6d00f0103`。

顶部无模式泄漏探针正确输出 `top_suction`，最大残差范数为 1.436 mm，专家回退为 0。侧吸探针输出 1.856 mm 的实质残差，但错误预测为 `top_suction`。这表明 R1 已摆脱零动作，却发生模式数据不均衡导致的顶部塌缩。

R1 的严格顶部闭环由 π0.5 真实路由至 `top_suction`，但任务失败。物体抬升 98.7 mm，未达到 120 mm 门；52 次推理中 Harness 回退 3 次，VLA 未验证终点到达。该结果不具备晋级资格。对应探针和严格闭环 summary 均保存在 `evidence/pi05_vla/`。

## D1：侧吸验证式恢复扩充

根据 R1 的模式塌缩，围绕已验证的直立圆筒侧吸恢复点设计 8 条小范围扰动，变化尺寸、质量、摩擦、初始位置和 5.5--6.5 mm 接触修正。8/8 回合均完整成功；放置误差为 6.2--7.1 mm，最大接触力不超过 9.51 N。失败轨迹未被伪造为动作示范。

为避免从顶部偏置变为侧吸偏置，训练集只预先选择第 1 和第 7 条侧吸轨迹，与原有两条顶部和一条侧吸轨迹合并。平衡数据集共有 5 个验证成功 episode、2,881 帧和 2,281 个非零残差帧。300/300 个 pregrasp 帧隐藏模式输入，任务进度覆盖 0 到 1。审计文件为 `evidence/pi05_vla/pi05-balanced-v2-dataset-audit.json`。

## R2：模式平衡数据上的 2,000 步 LoRA

R2 沿用 π0.5 base、LoRA rank 16、alpha 32、冻结视觉编码器和 RGB-D 合同，将训练步数增加到 2,000。数据路径为远端 `outputs/pi05-balanced-v2/pi05-residual-dataset-v2`，运行目录为 `/root/pi05-runs/mobile-pi05-balanced-2000-v3`，adapter SHA-256 为 `a0e71949560a8acd285914ad9dd8d52f5b34fb549a169c2ef4223b4e33ef6ffa`。

三样本无标签共识探针显示，R2 在顶部样本上以 3/3 票错误选择 `side_suction`，在侧吸样本上以 2/3 票错误选择 `top_suction`，因此未进入严格闭环。事后数据审计发现，2,881 帧中只有 300 个 pregrasp 帧隐藏模式输入，其余约 90% 帧向状态输入写入模式 one-hot。模型主要学习了复制训练时提示，而没有稳定学习 RGB-D 到抓取模式的映射。R2 被明确淘汰，不能作为后续训练起点。

## D2：托架模式局部 DOE 与接触记忆

冻结目录中协同托架占 42/105 回合，是 90% 目标的硬门槛。`mobile_pi05_cradle_doe_v2.json` 的 8 条局部候选均未完整成功；唯一越过固定 lift 接触率门的是右臂 `[0,+2,-2] mm` 残差，接触率为 0.50139，但抬升 79.15 mm，低于固定 80 mm 门。将残差改为 lift 全阶段立即生效的 v3 合同使抬升达到 81--106 mm，却把接触率降至 0.437--0.450，因此该合同被拒绝。共同增加 2--3 mm 抬升和单独增加左臂 1--3 mm 抬升分别解决了高度，但仍不能同时保持 0.50 接触率。这些开发结果全部保留为负证据，未进入训练集。

v6 在 Harness 中加入显式可消融的力感知托架接触记忆。lift 中失去真实托架接触时，安全层沿右托架表面法向累积补偿，最大权限为 5 mm；接触恢复时自动衰减，接触力达到 20 N 时加速退让，原有 35 N 安全门不变。该模块不选择抓取模式，也不生成任务动作，只约束 π0.5 残差执行的接触保持。三条候选中，左臂 1 mm 和 2 mm 正 Z 残差均完整成功，lift 接触率均为 0.50278，transport 接触率均为 1.0，抬升分别为 80.52 和 81.53 mm，放置误差分别为 14.1 和 13.0 mm，最大托架力为 32.98 N。两条成功轨迹进入训练数据；未达到抬升门的零左臂残差轨迹仍仅作为失败证据。完整记录见 `evidence/pi05_vla/pi05-cradle-*-collection.json`。

## D3：全阶段无泄漏三模式数据集

下一版合同将 80 维状态中的抓取模式输入在所有阶段置零，π0.5 必须从顶部 RGB-D、形状、尺寸、质量、密封状态、力历史、阶段和重试次数推断模式。lift 恢复标签同时改为与物理执行一致的 smoothstep 时序，manifest 固定记录 `mode_conditioning_policy=hidden_all_stages` 和 `lift_residual_supervision=smooth_stage_progress_v2`，训练脚本会拒绝不满足这两个字段的数据集。

合并数据包含 7 个完整验证成功 episode 和 4,053 帧，其中 3,327 帧具有非零接触残差。来源为两条顶部、一条原始侧吸、两条多样化侧吸和两条协同托架轨迹。审计确认 4,053/4,053 帧模式输入为零，600/600 个 pregrasp 帧无模式泄漏，任务进度覆盖 0 到 1，最大动作锚点重建误差为 0。manifest 与审计分别归档为 `evidence/pi05_vla/pi05-r3-hidden-all-dataset-manifest.json` 和 `evidence/pi05_vla/pi05-r3-hidden-all-dataset-audit.json`。

## R3a：合并分位统计故障与拒绝

R3a 于 2026-07-28 从固定 π0.5 base 重新开始，没有继承 R1 或 R2 adapter。配置为 LoRA rank 16、alpha 32、冻结视觉编码器、bfloat16、batch size 1、RGB-D、seed 11 和单张 AMD Radeon，原计划训练 3,000 步。训练从第一步开始只在约 `9.5564e14` 和 `5.7746e15` 两个 loss 之间切换，梯度范数约为 `7.09e7--3.16e8`，到第 87 步仍未改善，因此进程被主动停止，运行目录 `/root/pi05-runs/mobile-pi05-hidden-all-cradle-3000-r3` 被保留为拒绝证据。

差分检查表明，LeRobot 0.6.1 的数据集合并器会对各来源数据集的分位统计做按帧加权平均，而不是从合并后的全部真实帧重算分位数。R3a 首次加入协同托架数据后，`mode_cooperative_cradle_logit` 的统计变成 `min=-1`、`max=1`，但 `q01=q99=-0.4216629657`；`retry_index` 也出现同类矛盾。π0.5 使用 q01--q99 归一化，这两个变量通道因此被 `1e-8` 量级分母放大，解释了异常 loss。新增审计在 R3a 上明确返回这两个 `unsafe_quantile_width` 错误，证据为 `evidence/pi05_vla/pi05-r3a-normalization-audit.json`。该结果同时修正了早先“所有零方差通道导致爆炸”的初步假设：真正危险的是观测范围非零但归一化分位宽度坍缩；真实常量通道保持不变是安全的。

## R3b：真实帧重算统计与正式重训

数据管线现会在合并后直接读取全部 4,053 帧，重新计算 80 维状态和 14 维动作的全局统计。若变量通道的真实 q01--q99 仍坍缩，则只对该通道使用观测 min--max 作为确定性退化尺度；常量通道不添加噪声，也不伪造动作方差。训练入口和数据审计都会拒绝任何“观测范围非零但分位宽度小于等于 `1e-8`”的数据。R3b 使用同一组三个来源分片在新目录 `outputs/pi05-r3-hidden-all/pi05-residual-dataset-v3b-safe-stats` 重建，7 个 episode、4,053 帧和所有 parquet SHA-256 与 R3a 相同，仅统计和 manifest 改变。新审计错误为 0，证据为 `evidence/pi05_vla/pi05-r3b-dataset-manifest.json` 和 `evidence/pi05_vla/pi05-r3b-dataset-audit.json`。

从原始 π0.5 base 启动的 20 步数值探针没有继承任何旧 adapter。20 个 loss 全部位于 `0.103--2.270`，梯度范数位于 `0.321--1.777`；前五步与后五步 loss 中位数分别为 0.721 和 0.663，数值门通过。该探针只证明训练链路恢复正常，不证明机器人能力，完整序列记录于 `evidence/pi05_vla/pi05-r3b-probe20-summary.json`。通过该门后，新的 3,000 步正式训练已在 `/root/pi05-runs/mobile-pi05-hidden-all-cradle-3000-r3b` 启动，日志为 `outputs/pi05-r3-hidden-all/train-r3b-3000.log`。三模式探针、严格闭环和冻结 105 回合必须等待正式 checkpoint 完成后执行。

严格闭环另修正一项评测边界。训练数据中的接触残差定义为验证成功接触点相对名义锚点的差值，因此评测时不能再把同一专家修正量作为 `recovery_contact_offset_m` 或 lift offset 传给确定性目标，否则会形成专家修正与 VLA 残差的双重校正。`configs/mobile_pi05_r3b_strict_dev_v1.json` 将三种模式的专家接触、穿透和抬升修正全部置零，只保留物体属性、可观测重试状态和显式安全 Harness。该开发筛选只有在 π0.5 自主路由正确后才运行，且结果不回流训练集，也不计入冻结 105 回合。

R3b 完成后，三模式代表性探针为 2/3，16 个扩展观察为 13/16。顶部困难观察仍被路由为协同托架，因此没有资格运行严格闭环。扩展观察的 13/16 只能说明模型在部分训练分布附近学到模式差异，不能替代预注册困难观察门，更不能写成抓取成功率。

## D4：π0.5 可观测输入审计

对 LeRobot 0.6.1 的 `PI05Policy.forward()` 和 `predict_action_chunk()` 做调用链审计后确认，当前实现只将视觉张量和语言送入 π0.5 主干，配置中声明的 `observation.state` 没有进入策略前向。此前 80 维状态中的形状、尺寸、质量、逐杯密封、力历史、阶段和重试次数因此被静默忽略。这一发现推翻了“增加状态维度即可提供多模态条件”的假设，也解释了模式路由长期只依赖视觉和共享任务文本。

为了不泄漏抓取模式真值，新的输入桥只把可观测的形状、尺寸、估计质量、当前阶段和重试次数转换为逐帧模式盲语言。抓取模式 one-hot 继续在所有阶段置零，任务文本不出现 `top_suction`、`side_suction` 或 `cooperative_cradle`。逐杯密封和力历史暂未通过语言展开，保留为后续采用原生状态投影或专用 token adapter 的 E4 消融。

## R4：模式平衡普通 LoRA 的步数消融

R4 将 7 条独立验证成功轨迹重放为 10 个 episode 实例，共 5,871 帧和 4,785 个非零残差帧；三个重放实例只改变训练采样权重，不计为新的独立示范。训练继续使用共享模式盲指令、RGB-D、LoRA rank 16、alpha 32 和冻结视觉编码器。3,000、6,000 和 9,000 步 checkpoint 在同一组六个困难观察上均为 3/6，且错误模式完全一致：两个顶部观察和一个侧吸观察失败。继续堆训练步数没有改变路由边界，三个 checkpoint 均未进入闭环。

## R5：动作维度加权

R5 将三个模式动作维度的 flow matching MSE 权重从 1 提高到 4，其余 11 个动作维度保持为 1，并从固定 π0.5 base 重新训练 3,000 步。1,000、2,000 和 3,000 步 checkpoint 仍全部为 3/6；使用完全中性的推理提示复测 3,000 步结果也不变。该消融表明，仅在连续动作回归中放大模式维度不能解决完整扩散采样时的离散路由错误。

## R6：可观测状态语言桥

R6 将 5,871 帧映射为 30 条由形状、尺寸、质量、阶段和重试次数构成的模式盲任务文本，动作和图像字节保持不变。数据审计确认 7 条独立成功轨迹、3 个重放实例、所有模式状态输入隐藏且无模式名称泄漏。1,000、2,000 和 3,000 步 checkpoint 均为 2/6，顶部和侧吸观察全部失败，只正确路由两个托架观察。这证明单独增加可观测语言仍不足以让普通 flow matching 目标稳定分离三种模式。

## R7：随机扩散时刻的模式交叉熵

R7 在 R6 数据上增加权重为 1 的模式交叉熵，并保留模式维度 4 倍 MSE。交叉熵从训练时随机扩散时刻的去噪动作计算；训练日志中的模式准确率很快达到 1.0，但 1,000 步 checkpoint 只有 2/6，2,000 和 3,000 步也只有 3/6。原因是低噪声时刻的 `x_t` 已包含目标动作信息，辅助头可以沿扩散标签捷径恢复模式，而不必从 RGB-D 和语言判断模式。训练准确率因此不能作为完整纯噪声采样能力的证据。

## R8：纯噪声起点模式监督

R8 将同一模式交叉熵固定在扩散起点 `t=1`，使辅助损失面对纯噪声动作，只能依赖 RGB-D 和模式盲可观测语言。配置继续使用模式 MSE 权重 4、交叉熵权重 1、LoRA rank 16、alpha 32、冻结视觉编码器和 3,000 步预算。训练已完成 3,000/3,000 步，adapter SHA-256 为 `595da57f09994e44a430cb097089348451fae7edb16f6fa0548c007216f037be`。最后 500 步训练 mode accuracy 均值约为 0.993，但该帧级训练指标没有转化为新噪声和新观察上的稳定路由。

最初六观察探针按观察顺序递增扩散 seed，混杂了物体观察和随机噪声。评测现改为 common random numbers：六个观察均复用 `[20260727, 20260728, 20260729]` 三个 seed，并在工件中记录 `sample_seeds` 和 `sampling_seed_protocol`；汇总器会拒绝 seed panel 不一致的结果。重评后，1,000、2,000 和 3,000 步 checkpoint 仍全部只有 2/6，且均只正确路由两个协同托架观察。1,000 步时每个观察均为 3 票托架；2,000 和 3,000 步时每个观察均为 2 票托架、1 票顶部，侧吸从未获票。这证明失败不是旧 seed 顺序造成的，而是完整扩散模式输出主要受噪声支配，未稳定利用观察区分抓取模式。

3,000 步 checkpoint 的 `t=1` 直接流场诊断在相同 seed panel 下为 4/6：两个侧吸和两个托架观察正确，两个顶部观察均错误为托架。该诊断只说明辅助目标已学到部分观测条件化差异，不是闭环成功率。由于顶部目标本身尚未泛化，R8 没有资格进入三模式严格闭环。common-seed 工件位于远端 `outputs/pi05-r8-common-seed-eval/`。

## R9：多 epoch 纯噪声模式监督

R8 的 3,000 步只相当于 5,871 帧数据的约 0.51 epoch。R9 从固定 π0.5 base 重新开始，不继承 R8 adapter，将预算提高到 12,000 步（约 2.04 epoch），保持模式 MSE 权重 4、LoRA rank 16、alpha 32 和冻结视觉编码器，并把 `t=1` 模式交叉熵权重由 1 提高到 2。每 3,000 步保存 checkpoint，继续使用同一组六观察 common-seed 硬门。若 `t=1` 直接模式通过但完整扩散仍失败，后续候选才比较“π0.5 的 `t=1` 模式输出 + π0.5 完整扩散连续残差”的阶段解耦解码；模式仍必须来自 π0.5，禁止规则分类器或专家路由。

R9 训练目录为远端 `/root/pi05-runs/mobile-pi05-r9-high-noise-ce2-12000`，日志为 `outputs/pi05-r9-high-noise-ce2/train-r9-12000.log`。训练前额外审计了模式标签归一化：5,871/5,871 帧的 raw 模式 argmax 与 PI0.5 分位归一化后的 argmax 一致，三个模式通道均为 `q01=-1`、`q99=1`，模式状态泄漏为 0。因此 R8 的顶部失败不能归因于标签归一化重映射。证据归档为 `evidence/pi05_vla/pi05-r9-dataset-mode-normalization-audit.json`。训练完成后将自动运行 3,000、6,000、9,000 和 12,000 步 checkpoint 的 common-seed 完整扩散硬门与 `t=1` 诊断；任何离线诊断结果仍不得计作 VLA 闭环成功。

R9 已保存 6,000 步 checkpoint。GPU 无关静态审计为 `passed`：adapter 共 76 个 tensor、1,287,168 个参数，rank 16、alpha 32，状态/动作维数为 80/14，chunk 为 30，状态和动作均使用 quantile 归一化；adapter SHA-256 为 `7954ca8012b6d654883e4c58b84b77d72e449e69a595fa1128d31252f14bfa09`。审计同时确认该 checkpoint 不含 mode head 和 state token，符合 R9 对照定义。证据为 `evidence/pi05_vla/r9-common-seed/r9-step6000-checkpoint-audit.json`。训练仍在继续，未提前运行 GPU 路由筛选。

## D5：原生可观测状态 token 设计

LeRobot 0.6.1 的源码审计进一步定位到状态缺失的准确调用点：`PI05Policy.forward()` 和 `predict_action_chunk()` 均只从 batch 读取图像及语言 token，随后直接调用 `embed_prefix(images, img_masks, tokens, masks)`；`observation.state` 不参与训练或推理。权重兼容逻辑还会主动跳过 base checkpoint 中可能存在的 `state_proj`，而默认 PEFT 目标正则仍残留未实例化的 `state_proj` 名称。R9 因此继续作为“RGB-D + 可观测语言桥”的必要对照，不能被描述为已经使用逐杯密封和力历史。

后续 E4 候选预注册一个原生状态 token：先用现有分位统计归一化 80 维可观测状态，再零填充到配置的 96 维上限，通过可训练线性投影映射到 PaliGemma 前缀宽度，并作为一个有独立有效位的前缀 token 追加到图像与语言之后。状态中的三个抓取模式 one-hot 在所有阶段继续固定为零；训练数据中的左右名义接触锚点也固定为零，因为这些锚点由模式专用专家几何生成，而正式路由发生在模式专用 IK 之前，暴露它们会形成标签捷径。允许进入 token 的仅为机器人状态、逐杯密封、形状尺寸质量估计、阶段、重试次数和左右力历史。投影层必须作为 PEFT `modules_to_save` 完整保存，不能只依赖随机冻结基底上的 LoRA 增量；加载器必须从 adapter 元数据检测该模块并在载入权重前实例化。该候选需增加三项门禁：状态改变能改变纯噪声模式输出、模式 one-hot 与模式依赖锚点扰动不改变 token、保存后重载输出与保存前一致。只有这些门和六观察硬门通过后，才可作为 E4 进入严格闭环。

## 数据血缘修复

构建 R6 时发现 `contextualize_mobile_pi05_dataset.py` 曾使用硬链接复制 R4 数据，再直接覆写目标 parquet 和元数据。直接覆写硬链接会修改上游 inode，导致 R4 数据目录后来呈现 R6 的任务文本与 manifest，虽然 R4 训练日志仍明确记录训练当时的 `mode_neutral_shared_instruction_v1`。因此 R4 checkpoint 及其负筛选仍可作为工程诊断，但被污染的数据目录哈希不得用于最终确认性论文复现；若要纳入最终统计，必须从冻结源分片重新构建并重新训练。

数据构建器现改为“硬链接只读文件、临时文件原子替换所有可写 parquet/JSON”，并在输出 manifest 中记录源数据可写文件的前后 SHA-256 完整性检查。回归测试会比较构建前后的整个最小源数据树，确保派生数据集不能修改上游版本。该修复不改变正在训练的 R8 数据或 checkpoint，只修复后续自进化轮次的数据版本化。

## 预注册消融与统计

E0 为确定性 Harness 参考线，不作为 VLA 成绩。E1 为旧 π0.5 RGB/近零残差种子；E2 为模式均衡 π0.5；E3 为验证成功的非零接触恢复；E4 加入 RGB-D、逐杯密封和力历史；E5 加入验证式 failure replay 再训练。所有候选使用同一冻结 105 回合、同一物理参数和同一随机化顺序。独立实验单位是唯一 episode，帧、扩散采样和重试不作为独立样本。报告成功率与 Wilson 95% 区间，并使用 exact McNemar 检验配对差异。至少 95/105 成功、105/105 VLA 合格、专家回退为 0 且安全违规不增加的候选获得工程晋级；至少 100/105 才有资格声明总体成功概率超过 90%。

## 尚未满足的条件

目前没有任何 π0.5 checkpoint 达到 90%，也尚未产生真实冻结 105 回合 VLA 成绩。项目已经获得两条满足固定安全门的托架成功示范，但它们是离线专家生成的训练数据，不能计作 VLA 成绩。公开数据集实验、最终 Workshop 结果表和 SCI 论文结果段必须等待 R8 或后续候选通过三模式无泄漏探针、严格闭环和真实 VLA 冻结评测后再定稿。

# 2026-07-28 R9 完成、契约修复与 R10 晋级

R9 已完成 `12,000/12,000` 步并正常保存最终 adapter。最终 adapter SHA-256 为 `7f7875e702e16f036ea45f14de903114cc56f0b9612f48df487249d1d0b4723c`，包含 76 个 tensor、1,287,168 个可训练参数，LoRA rank 16、alpha 32，状态/动作维数为 80/14，chunk 30、执行窗口 10。训练结束后，正在运行的 Bash 包装器因同步更新过脚本而在尾声出现 `--wandb.enable: command not found`；训练本体与 checkpoint 未受影响，但尾部契约写入没有执行。后续脚本已改为在 GPU 训练前先写契约，并明确禁止再次修改正在执行的远端脚本。

使用原始固定数据集、base 与配置确定性重建 `PI05_TRAINING_CONTRACT.json` 后，契约 SHA-256 为 `ec26e712b0026ad27c12b4530c9743f8e4f1adb3d9084b537d0d35ed8eccea0a`，最终 checkpoint 静态审计通过。3k、6k、9k、12k 四个 checkpoint 的 `t=1` 诊断均为 `4/6`；完整 flow 均为 `3/6`。该结果说明增加训练步数没有修复 flow 通道路由，R9 不具备进入闭环的资格，训练 loss 和帧级模式准确率继续不作为能力指标。

完整 flow 工件同时暴露一个评测实现缺陷。协议要求每个观测复用相同的三组扩散种子，但旧 probe 只重置 `_calls`，实际种子却由 `_inference_calls` 驱动，因而六个观测依次获得 `[20260727..20260744]`。汇总器正确返回 `sampling_seed_panel_mismatch`，使 R9 fail closed。现新增 `reset_runtime_state()`，在每个观测前同时重置推理计数、一般调用计数、动作块队列、上一动作与力历史；相关本地和 Radeon 回归均为 `27 passed`。旧工件不改写并保留为审计证据，R10 及以后筛选必须逐观测记录相同的 `[20260727, 20260728, 20260729]`。

R9 四个 checkpoint 均未通过后，严格顺序门已启动 R10 前置的真实 π0.5 PEFT round-trip。R10 相对 R9 只新增 `parcel-pi05-contextualized-mode-head-v2` 与固定类别权重，仍从同一 π0.5 base 开始、保持 rank 16、alpha 32、12k 步、同一数据与同一 seed。模式必须由 π0.5 上下文化视觉语言特征输出，连续 residual 仍由原生 flow action expert 输出；Harness 不提供抓取模式或专家动作回退。round-trip 只证明 adapter 保存/重载和固定输入等价，不能计作闭环成绩。
# 2026-07-28 在线经验审计与混合解码改动

完成 OpenPI、LeRobot、π0/π0.5、FAST、OpenVLA、OpenVLA-OFT、Octo 和 RIPT-VLA 的定向检索，详细报告见 `docs/PI05_VLA_FINETUNING_ARCHITECTURE_REVIEW_CN.md`。公开证据支持归一化/动作语义硬门禁、多视角与状态输入、连续 action chunk，并提示 π0.5 LoRA 不能在无闭环证据时视为最终配方。

新增 opt-in fused mode head。该头从 π0.5 经 PaliGemma 上下文化后的视觉-语言 prefix 特征预测三类抓取模式，连续 14 维残差仍由 π0.5 flow action expert 生成。新增 mode head 和 state projection 均通过 PEFT `modules_to_save` 完整保存。控制器在带 mode head 的检查点上用 head logits 替换 flow action 的 `9:12` 路由通道，但不使用确定性专家分类器。

新增 `PI05_TRAINING_CONTRACT.json`，固定 80-D 状态、14-D 动作、残差语义、30 Hz、chunk 30、执行 10 步、基座版本、数据 manifest 和 normalization stats SHA-256。增强检查点缺少契约或指纹/维数/chunk 不一致时拒绝加载。R9 数据契约烟测 SHA-256 为 `ac16f4696cbee9ba2cdff69dde9f4acfc00291d5b178a91c44875ab562ab0493`。新增相关测试后，目标测试结果为 `11 passed`。

R9 未被改动，仍使用进程启动时加载的旧代码和原配置。记录时训练约 `3116/12000`；训练稳定不构成能力证据，继续等待完整 common-seed 筛选。

# 2026-07-28 增强 π0.5 PEFT 保存/重载门禁

根据官方 OpenPI 和 OpenVLA-OFT 配方复核，新增 `scripts/smoke_mobile_pi05_augmented_peft_rocm.py`。它不是轻量 mock，而是计划在 AMD 远端真实加载 π0.5 base，安装 fused mode head 与 observable state token，通过 LeRobot 的正式 `wrap_with_peft()` 构建 LoRA，并完成 adapter 保存、全新基座重载和固定输入等价性检查。固定输入同时覆盖合成 RGB、80 维状态、语言 token、扩散噪声和采样步数，比较 `state_embedding`、`mode_logits` 与完整 `action chunk` 的最大绝对误差。检查点还必须保留训练契约和预处理/反归一化工件。

脚本已同步到远端 `/workspace/parcel-sorter-opt-v1/scripts/`，语法检查和命令入口检查通过；状态 token、模式头、加权损失、训练契约和静态 checkpoint 审计的目标回归为 `15 passed`。真实 GPU round-trip 暂不与 R9 并发，避免改变正在运行的训练资源。最近一次 R9 观测约为 `5.4k/12k`，进程仍正常；其中一次预裁剪梯度峰值为 138.823，随后下一步恢复，不能据此判断策略能力。R9 完成并释放显存后，先执行该 round-trip 门，再决定是否启动 R10 fused-head 消融。

# 2026-07-28 模式头上下文化与架构版本门禁

启动 R10 前重新审计 fused mode head 的特征来源，发现初版直接池化 `embed_prefix()` 产生的原始 SigLIP/语言 embedding，没有利用 PaliGemma transformer 的上下文化输出。该实现仍属于 VLA，但视觉语言判别能力弱于设计预期。现已升级为 `parcel-pi05-contextualized-mode-head-v2`：训练阶段从 π0.5 原有的视觉语言/动作专家联合前向同时返回 prefix 与 suffix，模式头池化 contextualized prefix，flow residual 继续使用 suffix，因此不增加第二次训练主干前向；推理阶段用相同 PaliGemma prefix 路径生成 mode logits。

训练契约现同时记录 `state_token_protocol` 和 `mode_head_protocol` 并纳入 SHA-256。控制器加载增强 checkpoint 时按 adapter 中实际存在的模块要求精确协议；静态审计也执行相同检查。common-seed 筛选脚本现先为每个 checkpoint 生成静态审计，契约、归一化、模块权重或协议失败时不再运行 GPU 路由探针。新增单元测试以原始 prefix 全零、contextualized prefix 非零的反例证明模式头实际读取后者。相关目标回归为 `15 passed`，Python 与 Bash 语法检查通过，更新已同步远端且不会改变正在内存中运行的 R9。

# 2026-07-28 R9 到 R10 的断线安全顺序执行

新增 `scripts/advance_mobile_pi05_r10_after_r9_rocm.sh`。初始等待进程 PID `664430` 在尚未执行任何 GPU 工作时，因加入 contextualized head 类别平衡损失而取消，取消记录保存在远端 `outputs/pi05-r9-to-r10-gate-v1/CANCELLED.json`。更新后的 v2 以 PID `666622` 启动，等待 R9 训练 PID `658416` 和 common-seed 筛选 PID `659240`，等待阶段不占用 GPU。R9 四个 checkpoint 的六观察完整 flow screen 中只要有一个达到 `6/6`，执行器就写入 `DECISION.json` 后停止，要求先运行三条严格开发闭环，不启动 R10。若四个 checkpoint 全部失败，则先运行增强 π0.5 的真实 PEFT round-trip 和静态 checkpoint 审计；任一门失败都由 `set -e` 阻止 R10。

只有上述门禁全部通过，执行器才从固定 π0.5 base 启动 R10：LoRA rank 16、alpha 32、12,000 步、每 3,000 步保存，启用视觉语言 fused mode head 及权重 2 的独立模式交叉熵，关闭 flow-channel 模式交叉熵，并暂不启用 state token。这样 R10 与 R9 的主要架构差异是离散模式从完整 flow action 通道解耦，R11 才加入 state token。R10 也会自动挂接相同 common-seed 筛选。有效顺序执行日志为远端 `outputs/pi05-r9-to-r10-gate-v2.log`，PID 文件为同路径加 `.pid`，最终机器可读决策目录为 `outputs/pi05-r9-to-r10-gate-v2/`。启动、路由筛选和 round-trip 均不计作闭环成功率。

# 2026-07-28 R10 模式类别平衡

对 5,871 个训练帧重新审计后，顶部吸附为 2,572 帧（43.81%），侧面吸附为 2,127 帧（36.23%），协同托架仅 1,172 帧（19.96%）。episode 数量看似为 4/4/2，但不能代替逐帧损失分布；普通交叉熵会让托架错误的总训练贡献偏低。R10 因此预注册按 `N/(3 n_c)` 计算的类别权重，按 `top_suction`、`side_suction`、`cooperative_cradle` 顺序分别为 `0.7608864697`、`0.9200752233` 和 `1.6697952218`。这使每类在完整数据上的理论总权重相等，不通过复制轨迹伪造新的独立样本。

权重由 `diagnose_mobile_pi05_mode_dataset.py` 从真实 parquet 重新计算，证据为 `evidence/pi05_vla/pi05-r10-mode-balance-audit.json`；训练入口打印权重，训练契约保存权重并纳入指纹，静态审计回读权重。保留相同 contextualized head、但不使用类别权重的候选作为后续优化消融，不与主 R10 同时占用 GPU。相关目标回归为 `16 passed`。

# 2026-07-28 action chunk、idle 审计与证据边界修正

复核当前 LeRobot π0.5 源码与 RTC 文档后确认：训练使用 30 步 action chunk，但现有移动控制器将 `n_action_steps` 强制为 1，每次低频推理只使用 chunk 的第一个动作并保持到下一次 3 Hz 推理。训练工件中“执行 10 步”此前只是计划契约，不是已经验证的运行时事实。为避免在 R9 运行期间改变筛选协议，新增 `aggregate_pi05_residual_action_chunk()` 与 opt-in `chunk_execution_steps`；默认仍为 1。后续 E5b 将比较首动作保持、10-step 窗口聚合、真实 30 Hz chunk executor 和 RTC，并记录推理延迟、chunk 边界跳变、接触力与完整成功率。

根据 OpenPI DROID 的官方经验，数据审计新增 largely-idle chunk 指标，但暂不自动过滤。本项目的零 residual 可能是正确安全动作，且模式 logits 恒为非零，因此审计只读取动作 `0:9`、吸盘状态变化和 progress 跨度。是否过滤必须用相同训练种子和相同开发集做 matched ablation；不能因追求非零比例删除验证成功恢复轨迹。

远端审计实际结果为 5,871 个训练起点中 5,861 个 informative chunk、10 个 largely-idle chunk，idle 比例仅 `0.001703`；4,765 个 chunk 满足 residual 活跃门，5,861 个含吸盘/progress 转变。审计状态通过，量化归一化没有不安全维度，证据保存为 `evidence/pi05_vla/pi05-r10-action-chunk-activity-audit.json`。据此不再把 idle 过滤列为近期训练候选，算力转向 state token、rank 32、wrist RGB-D 和 chunk executor/RTC。

当前 common-seed 六观察均来自训练 parquet，已在新 probe 工件中标为 `training_distribution_development`。即使达到 `6/6`，也只授权三条开发闭环；真正 held-out 路由需要从未用于训练的物体尺寸、质量和形状初态单独采集，并以 `heldout_observation` 标记。最近一次远端观测约为 `7.0k/12k`，R9 仍在运行，R10 顺序门控仍在等待。没有新的闭环成功率，也没有证据支持 90% 声明。

# 2026-07-28 冻结 held-out observation panel 与 R11 顺序门

新增 `configs/mobile_pi05_heldout_observation_v1.json`，在任何 checkpoint 结果可见前冻结 12 个未见物理上下文，顶部、侧面和协同托架各 4 个。顶部覆盖 micro box、flat mailer、electronics box 和 USPS small flat-rate；侧面覆盖四组未见直立圆筒尺寸/质量；托架覆盖横放 mailing tube、USPS medium flat-rate、大圆筒和大方箱。所有任务文本均不包含抓取模式词。该面板只允许使用每个 episode 的第一个 pregrasp RGB-D/状态观察，任何动作、恢复和结果都禁止进入训练。

`audit_mobile_pi05_observation_panel.py` 读取真实 R10 训练 parquet 后确认：训练集包含 5 个唯一物理上下文，冻结面板包含 12 个唯一上下文，精确物理签名重叠为 0；每种模式均为 4 个，隐藏模式标签与冻结物理路由一致。审计 SHA-256 为 `ee637ac65004599c56df7e93c127307349847385ce55d716691cf886883d79bf`，证据见 `evidence/pi05_vla/pi05-heldout-observation-v1-isolation-audit.json`。该结果只证明配置隔离，RGB-D 初态尚未采集，因此不能报告 held-out 模型准确率。

新增 `advance_mobile_pi05_r11_after_r10_rocm.sh`，远端等待 PID 为 `667475`。它等待 R9→R10 门和 R10 四个 checkpoint 筛选；若 R9 或 R10 任一 checkpoint 达到训练分布完整 flow `6/6`，则停止并要求先做严格开发闭环。只有 R10 四个 checkpoint 全部失败，才以与 R10 相同的 base、数据、rank 16、类别平衡 fused mode head 和 12k 步启动 R11，唯一新增因素是 `parcel-pi05-state-token-v1`。最近一次 R9 观测约为 `8.1k/12k`；仍无闭环能力结论。

# 2026-07-28 R12 rank-32 单因素顺序门

新增 `scripts/advance_mobile_pi05_r12_after_r11_rocm.sh`。该门首先等待 R10→R11 编排器以及 R11 训练、post-screen 全部结束；若上游在 R9/R10 已要求严格闭环，或 R11 任一 checkpoint 达到训练分布完整 flow `6/6`，则写入机器可读决策并停止，不启动 R12。只有 R11 四个 checkpoint 全部失败时，才允许进入 rank-32 烟测和训练，因此不会与 R9/R10/R11 争抢单张 Radeon GPU。

R12 与 R11 的唯一训练因素是 LoRA rank 从 16 提高到 32；alpha 固定为 32，base revision、R10 数据、seed 11、12,000 步、3,000 步保存频率、类别平衡 contextualized mode head、observable state token、冻结视觉编码器和首动作保持执行协议全部锁定。`audit_mobile_pi05_checkpoint.py` 新增期望 rank/alpha 硬门，任何 adapter 元数据不符都会在 GPU 路由筛选前失败。增强 PEFT round-trip 现在记录设备总显存、峰值 allocated 和 reserved 显存；该数字只代表真实基座加载、增强模块、flow 推理和保存重载的推理峰值，不冒充完整反向训练显存，也不构成能力证据。

2026-07-28 再次读取 OpenPI LIBERO、OpenPI DROID、OpenVLA-OFT 与 LeRobot π0.5 官方主分支。可复核事实仍为：OpenPI π0.5 30k LIBERO 平均 `96.85%`；DROID 官方说明尚未获得表现良好的 LoRA 策略；当前 LeRobot π0.5 已出现 `RTCProcessor` 接口；OpenVLA-OFT 继续采用连续 action chunk 与本体/多视角输入。它们支持本项目的 rank、state、wrist 和执行器消融顺序，但不支持提前声称本项目达到 90%。最近一次 R9 观测约为 `8.5k/12k`，仍没有新的闭环 VLA 成绩。

R12 顺序门已在 Radeon 远端以 PID `668319` 启动，日志 PID 文件为 `outputs/pi05-r11-to-r12-gate-v1.log.pid`，机器可读决策目录为 `outputs/pi05-r11-to-r12-gate-v1/`。等待阶段不执行 GPU 运算。启动后验证 R9 约为 `8,880/12,000`，训练显存日志为 `9.22 GB`；Radeon 上 28 项相关回归通过。该进度和显存只说明训练链正常，不是策略能力或成功率证据。

# 2026-07-28 真实 30 Hz action-chunk 执行路径

控制链审计确认，原 `first-action-hold-v1` 每次推理只执行 chunk 第一项，`pi05-window-aggregate-v1` 则把若干未来 residual 平均为一个低频命令；二者都没有保留 π0.5 action chunk 的时间顺序。新增 opt-in `pi05-open-loop-queue-v1`：每次完整 flow 推理保留前 N 个有序 14-D residual，在接下来的 30 Hz 控制帧逐项执行。每帧都基于最新机器人状态、接触力、密封状态和当帧确定性参考重新运行 residual projection 与 Harness；缓存的只是 VLA residual，不是绕过安全层的绝对关节命令。

阶段变化、模式路由投票和显式强制重规划都会清空队列。融合模式头的三个 logits 在同一 chunk 内保持一致，而底盘/双臂 residual、吸盘意图和进度保持逐步预测值。遥测新增 `inference_performed`、`inference_call_index`、`chunk_step_index`、`chunk_steps_remaining` 和 `residual_boundary_l2`；评测汇总分开报告 30 Hz 控制选择次数与真实 GPU 推理次数，延迟统计只使用真实推理帧，避免缓存帧的 0 ms 稀释结果。默认仍为首动作保持，当前训练筛选完全不变。该实现只证明执行接口存在，必须等待合格 checkpoint 后做配对闭环消融，不能据此报告成功率提升。

新增 `audit_mobile_pi05_rtc_runtime.py`，对当前 Radeon 环境中的 LeRobot 版本、`PI05Config.rtc_config`、`RTCConfig` 字段、`predict_action_chunk()`/`sample_actions()`/`RTCProcessor.denoise_step()` 签名及三个 RTC 参数的传递路径做静态运行时审计。审计同时强制确认 `select_action()` 带有 RTC 禁止门，防止错误地打开配置却继续走单动作 API。该工件只验证接口兼容性；RTC 仍需在顺序 chunk 取得真实推理延迟、边界 L2、力违规和成功率基线后再接入。

Radeon 实测审计状态为 `passed`，LeRobot 版本为 `0.6.1`，三个必需参数 `execution_horizon`、`inference_delay`、`prev_chunk_left_over` 均由 π0.5 `sample_actions()` 转发给 `RTCProcessor.denoise_step()`，且 `select_action()` 的 RTC 禁止门存在。机器可读证据保存为 `evidence/pi05_vla/pi05-rtc-runtime-audit.json`。顺序 chunk 与相关遥测的扩展回归为 `48 passed`；这些仍属于接口与回归证据，不是闭环能力证据。

冻结 `configs/mobile_pi05_chunk_runtime_ablation_v1.json`，将运行时比较固定为 30 Hz 控制、3 Hz 推理和 10 步执行窗口。C0 为首动作保持，C1 为 10 步窗口平均，C2 为 10 个 residual 按 30 Hz 顺序执行；三组使用同一 checkpoint、同一三条严格开发 episode、同一模式投票和同一 Harness。批量采集器现已透传 chunk 协议与步数。C2 只有在密封率或完整成功率提高且力违规不增加时才允许进入 RTC；该开发消融不替代最终冻结 105 回合。

配对复核发现 Force Memory 原按策略调用次数采样，C0/C1 的 3 Hz 与 C2 的 30 Hz 会把 6 样本记忆窗口从约 2 秒变成 0.2 秒，形成运行时混杂。现将接触力观测独立为 30 Hz 控制帧采样，策略选择只消费已经更新的历史而不重复写入；不经过外部控制循环的单步 probe 仍从输入状态自动采样。这样三组的 Force Memory 时间尺度一致，action chunk 才是主要处理因素。

新增可恢复执行器 `run_mobile_pi05_chunk_runtime_ablation_rocm.py`。它要求传入已通过的 route screen，并校验 screen 内 checkpoint 路径与待测 checkpoint 完全一致、准确率为 1 且专家回退为 0，防止用模型 A 的门票评测模型 B。runner 依次执行 C0/C1/C2，固定单 GPU、同一三条 episode、3 Hz 推理和 10 步窗口，分别生成 collection summary、VLA campaign audit、哈希链接的 arm summary 和总结果。每个 arm 还会回读实际运行时协议与步数，配置漂移时失败。跨 chunk 的 residual L2 现已聚合到回合 policy summary，延迟只统计真实 GPU 推理帧。

# 2026-07-28 原生 π0.5 自主恢复回放记录

审计旧自进化链后确认，旧 runner 仍可切换到 SmolVLA/PASH，旧 dataset writer 保存 43D 状态和 19D 确定性绝对动作，后处理脚本再根据 recovery offset 构造 residual；它们不能证明训练标签来自 π0.5 自主恢复。因此新增 `mobile_pi05_dataset.py`，评测控制器直接暴露 Harness 前的原始 14D π0.5 residual 与 80D 可观测状态，writer 逐帧保存 RGB-D、stage、task、privileged audit state，并标注真实推理、低频保持、inference call 和 chunk step。阶段切换现在强制立即重新查询策略，防止旧阶段动作保持到新阶段。

episode 提交门固定为：完整任务成功、checkpoint 类型为 π0.5、14D residual 契约、`pi05_residual` 执行、VLA 自主模式路由、VLA goal verdict 实际验证、专家回退 0、紧急停止 0、35 N 力违规 0、至少一帧非平凡底盘/双臂 residual。任一条件失败都清空 LeRobot episode buffer，失败观测不能成为 BC 标签。manifest 绑定 `adapter_model.safetensors`、训练契约、评测 summary 的 SHA-256，并明确记录原始 residual 未被 Harness 反推或专家动作替代。Radeon 语法检查和 writer/chunk/Harness 定向回归为 `26 passed`。这只证明数据链满足论文方法定义，不是自进化增益或成功率证据。

同日一手资料复核：OpenPI π0.5-LIBERO 仍为全量 `30k/batch 256`、平均 96.85%；DROID 文档明确 LoRA 尚未得到良好策略；OpenVLA-OFT 的高分配方包含 rank 32、连续动作、8 步 chunk、腕部图像和 proprio；RTC 仅处理延迟；RIPT-VLA 的 97.5% 属于仿真交互式后训练。当前 R9 最近观测为 `11285/12000`，约 94%，无真实闭环 π0.5 成绩，不能报告达到 90%。

# 2026-07-28 R10 完成、失败归因与 R11 启动

R10 已完成 `12,000/12,000` 步，最终 adapter SHA-256 为 `ed14d1eb776ffaae71b80467f2ce9a32d3e33eb4bd78688ad91ecfeebe8cd390`，训练契约 SHA-256 为 `02997196a20e0e03ec15063ac5c5c6d74a73f09a296d17a647fc1563ccefce59`。R10 相对 R9 的主要处理因素为 contextualized fused mode head 和预注册类别权重；状态 token 关闭，连续 residual 仍由 PI0.5 flow action expert 输出。

使用相同 common-random-number 协议筛选 3k、6k、9k 和 12k 四个 checkpoint。四者均为 `2/6`：顶部吸附 `2/2`，侧面吸附 `0/2`，协同托架 `0/2`，所有采样一致投票为 `top_suction`。探针同时满足有限输出、实质 residual、零专家回退和真实 PI0.5 检查，但模式不正确，因此 fail closed，未运行严格闭环。训练 batch 中出现的高 mode-head accuracy 和正 margin 没有转化为冻结观察路由能力，说明 masked-mean fused head 仍主要学习了局部序列或类别先验，不能据此报告 VLA 成功率。

R10 四个 checkpoint 全部失败后，顺序门于 2026-07-28 07:34 启动 R11。R11 与 R10 保持相同 base revision、数据、seed 11、rank 16/alpha 32、类别权重、12k 步、每 3k 保存和冻结视觉编码器，唯一新增因素是 `parcel-pi05-state-token-v1`。形状、尺寸、质量等可观测状态通过可训练投影注入 PI0.5 prefix，离散模式仍由 VLA fused head 自主输出，Harness 不提供模式真值或专家回退。GPU 训练 PID 为 `700669`，post-screen PID 为 `700457`；R12 rank-32 门 PID `698222` 继续等待。启动和训练进度不计作闭环成绩。

# 2026-07-28 R13 模式头池化预注册

R10 的四个 checkpoint 均稳定塌缩为顶部吸附，说明 masked-mean 模式头没有从冻结观察中提取可迁移的模式判别特征。R13 预注册为 R11 的单因素架构消融：保持 base、数据、seed 11、rank 16/alpha 32、类别权重、state token、12k 步和 Harness 全部不变，只将模式头池化从全部有效视觉语言 prefix 的 masked mean 改为最后一个有效语言 token。该 token 已经通过 PaliGemma 因果注意力聚合前序图像、语言和可观测状态上下文，同时避免大量图像 patch 在简单均值中稀释任务级决策。

新增协议 `parcel-pi05-last-language-token-mode-head-v3`。训练、独立推理、PEFT round-trip、训练契约、静态 checkpoint 审计、控制器加载和遥测必须使用同一协议；v2/v3 不允许互相加载。R13 只在 R11/R12 均未通过四 checkpoint 的 `6/6` 路由门后运行；若上游候选合格则停止 R13，先做零专家回退严格闭环。独立实验单位仍是 episode，六观察只作开发门，不作成功率或泛化结论。核心协议和既有 VLA 归因回归共 `48 passed`，真实 4B PEFT round-trip 留待单 GPU 释放后执行。

经过临时隔离目录验证后，v3 代码已通过原子文件替换同步到 Radeon 实际仓库；正在运行的 R11 继续使用启动时加载的 v2 代码与权重，后续 R11/R12 默认仍为 v2，只有显式环境变量 `MOBILE_PI05_MODE_HEAD_POOLING=last_language_token` 才启用 v3。远端实际仓库再次获得 `48 passed`，Bash 语法和 Python 编译检查通过。R13 fail-closed 等待门 PID 为 `715036`；它只等待 R12 门 PID `698222`，等待期间不占用 GPU，也不构成训练或能力证据。

正式契约入口已在真实 R6 数据集上完成 R13 烟测。生成的契约固定 80-D 可观测状态、14-D residual、chunk 30、执行窗口 10、state token v1、last-language-token mode head v3 和预注册类别权重；契约内部指纹为 `b420f2d8a3ca33cbd08ec8ca01510cf029194fa34c8b83d8e4f9f01208ef5629`，文件 SHA-256 为 `a2a13b96a4ee2458280be9e80003dec87e5346dacf5aae7116d88da1aadc7327`。证据归档为 `evidence/pi05_vla/pi05-r13-training-contract-smoke.json`。该工件只证明正式入口能生成一致契约，不证明 PEFT、路由或闭环能力。

# 2026-07-28 Held-out 初始观察采集与位置区组

冻结观察面板原先按执行模式沿用不同的工作台位置：协同托架默认位于中央，其他模式默认位于左侧。这会使模式与图像位置混杂，即使对象几何完全未见，模型也可能通过位置捷径获得虚高路由准确率。新增 `mobile_pi05_heldout_workspace_block_v1.json`，将 `-0.68/-0.45/-0.22/0.00 m` 四个 pedestal X 位置以循环区组分配给每一种模式；真实冻结面板审计通过，区组 SHA-256 为 `068211369c6e71ce41616a4a0d59e9a3b863e79b2346bdac25ba9ade37aa90d3`。

新增 held-out capture 合同、采集器和集合审计。每个 episode 只在物体稳定、策略尚未执行的 pregrasp 时刻保存一次 overhead RGB、metric depth 和 80-D 可观测状态；状态 `52:55` 三个模式通道强制为零，文件不含 action、expert action、recovery 或 outcome。sidecar 绑定任务、隐藏评测标签、物理上下文、工作区区组和观察 SHA-256；集合 manifest 必须与 12 个冻结 episode 一一对应并限制所有相对路径留在 collection 根目录。目标测试为 `7 passed`，实际仓库 Python/Bash 语法和三个 CLI 入口通过。

真实采集不与训练争用 Radeon。等待门 PID `721367` 先等待 R13 门 PID `715036`；若 R13 被启动，还会继续等待其训练和 post-screen PID 全部结束，再依次生成 12 个初始观察并执行集合审计。采集完成仍不会自动加载或探测任何 checkpoint，且 `training_use_allowed=false`。该流程是评测隔离证据，不是 held-out 准确率或闭环能力证据。

R11 3k checkpoint 已无 GPU 静态审计通过：adapter SHA-256 为 `c18784fc0ea8e5ee82d463a2a599a5fa1e353dc65a110f0113415e4ba8b4a27c`，包含 state projection 和 contextualized mode head，rank 16/alpha 32、80/14-D 契约、类别权重与归一化一致。证据归档为 `evidence/pi05_vla/pi05-r11-step3000-static-audit.json`。静态完整性不代表路由能力，完整 flow screen 仍等待训练结束后运行。

新增 one-shot held-out 路由评测器。只有开发路由与严格开发闭环已经冻结的单个 checkpoint 才能运行；12 个观察必须全部模式正确、每条至少 3 个共同随机种子采样、有限输出、实质 residual、捕获哈希通过且专家回退为 0。工件固定写入 `checkpoint_selection_allowed=false`：held-out 失败只能报告，不允许据此继续选择 checkpoint 或修改模型。held-out 汇总、捕获与面板联合回归为 `10 passed`，实际 Radeon 仓库编译和 CLI 检查通过；当前尚未运行任何 checkpoint 的 held-out 推理。

# 2026-07-28 冻结 105 回合的 policy-authority 声明门

复核最终配对晋级器后确认，原实现虽要求专家 fallback 为 0，却只要求整个 campaign 至少出现一次实质 residual，也没有把 `policy_authority` 与 `expert_reference_used` 纳入纯 VLA 声明。这会允许 hybrid expert-reference residual campaign 在统计上通过后被误写为纯 VLA。现已将实质 residual 门提高为 105/105 回合全部满足，并要求每回合 authority 明确属于 `hybrid_expert_reference_plus_vla_residual` 或 `absolute_vla_action_candidate`；未知归因直接阻止晋级。

统计输出保留系统级 `promotion_gate_passed` 与 `paper_claim`，但 `paper_claim.claim_scope` 必须明确 hybrid、absolute 或 mixed。新增独立 `pure_vla_promotion_gate_passed` 和 `pure_vla_paper_claim`：只有全部 105 回合均为 absolute VLA、`expert_reference_used=0`、fallback=0、emergency stop=0、力违规不增加、全部有实质 residual，且至少 100/105 成功通过单侧 exact-binomial 检验时才为真。相关晋级与 campaign 回归为 `12 passed`。这项修复不改变已经运行的 hybrid 控制器，只修正论文声明和晋级边界。

冻结消融配置同步更新：R9/R10 标为路由失败，R11 标为运行中，R12 为 rank-32 顺序候选，R13 为 last-language-token 单因素候选，腕部 RGB-D 顺延为 R14。held-out 面板角色从 candidate selection 更正为 one-shot final generalization audit，明确禁止用测试面板继续选 checkpoint。

# 2026-07-28 腕部 RGB-D 数据与推理合同

R14 的多视角因素先只落到数据与运行时接口，不提前启动训练。`MobileBimanualFrame` 与验证式 `PI05AutonomousResidualFrame` 新增可选左腕 RGB/metric-depth 字段；两个 LeRobot writer 只有在 `include_wrist_rgbd=true` 时才声明并强制保存 `left_wrist_rgb`、`left_wrist_depth` 与 `left_wrist_depth_rgb`。默认 overhead-only 特征集合完全不变，因此 R11、R12 和 R13 仍是可比较的单视角消融。

仿真运行时新增显式 `--wrist-rgbd` 开关。腕部相机根据左末端当前位姿逐帧更新，再把同一时间点的 wrist RGB-D 同时送入模式路由、闭环 PI0.5 推理、专家轨迹记录和通过资格门的自主 replay 缓冲。不开启该开关时不创建或渲染腕部相机。该实现先在远端隔离副本完成 Python 编译、11 项 writer/replay 回归和完整 CLI 解析，再同步到实际 Radeon 仓库；同步后的 11 项远端回归也通过。

上述结果只是 R14 输入通道的工程证据，不是模型能力证据。当前没有腕部 RGB-D 训练 episode、R14 checkpoint 或腕部闭环结果，不能把它写成 E4 性能提升。R11 在 2026-07-28 08:42 的最近训练观测约为 `7501/12000`，仍须等待完整训练、四 checkpoint 冻结路由筛选以及后续严格零专家回退闭环。

为保证 R14 真正只改变视觉输入，新增端到端视觉键指纹。采集器显式转发 `--wrist-rgbd` 并在 collection summary 写入 modality；残差转换从源 LeRobot `info.json` 推断完整视觉合同并写入 manifest；训练入口依据 `MOBILE_PI05_WRIST_RGBD=0/1` 构造精确的两键或四键 `policy.input_features`，同时拒绝数据与开关不一致；不可变训练契约记录 `policy_visual_modality` 和有序视觉键；静态 checkpoint 审计及运行时控制器再将 checkpoint 配置与该契约逐项核对。缺一只腕部通道也会 fail closed。

该改动在临时隔离目录通过 27 项相关回归、训练 Bash 语法和采集 CLI；随后使用新验证器重新审计已有 R11 3k checkpoint，overhead RGB-D 旧契约兼容且审计仍为通过。文件哈希核对后才替换远端实际仓库，同步后的视觉合同核心测试再次通过。此过程不接触 R11 已加载的进程，也不改变 R11 数据或模型。08:54 最近训练观测约为 `8733/12000`，尚未执行完整 flow screen 或闭环。

为避免多视角 treatment 与重新采集的控制轨迹混杂，新增 `audit_mobile_pi05_visual_pairing.py`。在任何 R14 训练前，它要求 baseline modality 恰为 overhead RGB-D、treatment 恰为 overhead+wrist RGB-D，并逐帧比较 episode/frame/task/stage 索引、80-D 状态和 14-D 动作；若同时提供两份 collection summary，还要求成功 episode 顺序与完整物理参数相同。默认状态和动作绝对容差均为 `1e-6`，任何超限帧均 fail closed。三项单元测试覆盖精确配对、动作漂移和帧数变化。该审计只隔离实验因素，不衡量 VLA 能力。

R11 9k checkpoint 的无 GPU 静态审计已通过，adapter SHA-256 为 `dc61d349a08e53ec8373ce58af451c396f5b68f57633c6f61b5fd9b1aa4cb2ad`，rank 16/alpha 32、state token、mode head、80/14-D 和 overhead RGB-D 两键均与冻结契约一致。证据归档为 `evidence/pi05_vla/pi05-r11-step9000-static-audit.json`；完整 flow routing screen 仍等待 12k 训练和 post-screen，不能将此完整性结果计作成功率。

# 2026-07-28 自进化 replay 的 authority 分层

原 PI0.5 自主 replay 门已经要求完整成功、模式由 VLA 路由、VLA goal verdict、fallback=0、force violation=0 和实质 residual，但没有记录名义动作来源。由于当前 residual 控制实际执行 `expert reference + PI0.5 residual`，将这类成功写成“PI0.5-only autonomous experience”会混淆动作归因。新增统一 `mobile_policy_attribution.py`，从逐帧遥测汇总 canonical `policy_authority`、`expert_reference_used`、reference semantics 和内部一致性；campaign summarizer 将这些标准字段直接传给配对晋级器。

replay qualification 现拒绝 unknown authority，并在 manifest 中同时写入 `accepted_for_behavior_cloning`、`replay_authority_scope` 与 `accepted_as_pure_vla_experience`。经过验证的 hybrid 成功仍可作为 14-D residual 行为克隆标签，因为保存的是 Harness 前原始 PI0.5 residual；但其 pure-VLA 标志固定为 false。只有 `absolute_vla_action_candidate`、无专家参考、无 fallback 且通过全部成功安全门的 rollout 才能标为纯 VLA 自进化经验。自主恢复报告协议升级为 v2，不再使用 “PI0.5-only” 描述，并分别报告 system eventual success 与 pure-VLA eventual success。联合 replay、recovery、campaign 和 promotion 回归为 `25 passed`。

# 2026-07-28 R11 训练完成与运行时回归修复

R11 在 09:23 完成 `12000/12000` 步，日志出现 `End of training`。3k/6k/9k/12k checkpoint 已完整保存；训练完成本身不计为 VLA 能力证据。

原 post-screen 加载 3k checkpoint 后，在首个完整扩散调用的遥测汇总处触发 `NameError: config is not defined`。根因是阶段化 action-chunk 改动在控制器 `select()` 中引用了构造函数的局部变量 `config`；此前 47 项以纯函数和静态合同为主的测试没有执行真实 GPU `select()`，因此未覆盖该路径。该错误只中断评测编排，没有停止训练、删除权重或产生可计分结果。

修复将窗口聚合、开放队列和遥测三处 chunk horizon 解析统一收敛到 `_effective_chunk_execution_steps()`，只读取 `self._config.chunk_size`。新增控制器实例回归，隔离副本与实际 Radeon 仓库的 `test_mobile_harness.py + test_mobile_pi05_chunk_runtime_ablation.py` 均为 `27 passed`。在同步实际仓库前，使用隔离源代码对 R11 9k checkpoint 完成一次 overhead-only 全扩散烟测和一次 `t=1` 纯噪声烟测：两者均报告视觉键恰为 overhead RGB-D，两者输出均有限且没有 expert fallback。单观察结果不能充当冻结六观察筛选或闭环成功率。

由于旧 post-screen 输出目录已包含部分失败工件且协议禁止覆盖，修复后使用新目录 `outputs/pi05-r11-common-seed-eval-v3/` 重新启动四 checkpoint screen，PID 为 `729358`。原 R12/R13 门在缺少四份 screen 时已 fail-closed 退出；只有新 screen 全部完成后才会按原预注册顺序恢复后续训练或进入严格开发闭环。

# 2026-07-28 R11 路由通过但严格闭环失败

R11 的 3k、6k、9k 和 12k checkpoint 在修复后的完整 flow screen 中全部达到 `6/6`，每个 checkpoint 的 top/side/cradle 均为 `2/2`，每条观察的三 seed 投票一致；四个 checkpoint 的 `t=1` 诊断也均为 `6/6`。这些是训练分布开发路由证据，不是抓取放置成功率。

四者在预注册指标上完全并列。为避免使用 held-out 或闭环结果挑 checkpoint，新增 `pi05-earliest-passing-route-checkpoint-selection-v1`：只有四份 screen 使用同一数据和 seed panel、逐份哈希且达到完整 `6/6` 时，才选择最早达到门槛的训练步。规则选中 3k，adapter SHA-256 为 `c18784fc0ea8e5ee82d463a2a599a5fa1e353dc65a110f0113415e4ba8b4a27c`；工件明确记录 `heldout_observations_accessed=false` 与 `closed_loop_results_accessed=false`。选择器 3 项回归通过。

首次严格闭环启动没有导出仓库 `src` 路径，三个 evaluator 均在仿真前以 `ModuleNotFoundError` 退出。该表面 `0/3` 已写入 `INVALID.json`，固定 `closed_loop_rollouts_executed=false`，不得计作模型结果。新目录 v2 使用显式 Python 环境重跑，保留旧工件且不覆盖。

有效 v2 结果为 `0/3`。三个 episode 的模式均由 PI0.5 正确选择并执行，抓取和抬升均成功，force violation 为 0；但三个 episode 均在 `transport_success` 失败，每条发生一次专家 fallback，VLA goal arrival 均未验证。micro box、upright canister 和 large carton 的终点误差分别约为 `0.119/0.194/0.240 m`。campaign 的 attribution 为三条 `hybrid_vla_residual_with_expert_reference`，纯 VLA 合格数为 0。

数据审计给出直接因果链：R11 使用的 5,871 帧数据把 `base_residual_vx_m_s`、`base_residual_vy_m_s`、`base_residual_vyaw_rad_s` 全部写为常数零；六项统计 min/max/mean/std/q01/q99 的前三维均为零。闭环 trace 中各阶段 PI0.5 底盘 residual 范数约为 `1e-9`，所以策略从未获得运输动作监督，运输依赖专家参考速度。继续 R12 rank 或 R13 池化不会修复零标签，故二者按因果停止，不消耗 GPU。

后续新建 B0 absolute-VLA 实验族：从固定 PI0.5 base 重新训练，不继承 R11 adapter；输入为 80-D mode-blind 可观测状态，最后六维只能来自当前末端位姿，禁止由目标 action 反推 contact anchor；输出为 19-D 可执行绝对动作、3-D VLA 模式 logits 和进度，共 23-D。运行门要求 `policy_authority=absolute_vla_action_candidate`、`expert_reference_used=false`、fallback=0，只有该合同的完整成功才能进入纯 VLA 自进化与最终 105 回合声明。

# 2026-07-29 B3-SW 预注册与持久化迁移

B3 增量 SE(3) 在六个配对动作保真单元中只改善 `2/6`，回退 `4/6`，12k checkpoint 的平均归一化位姿误差改善为 `-0.546`，因此未进入闭环。后续候选命名为 `B3-SW`，`B4` 保留给验证式 recovery/advantage learning。B3-SW 回到 B2 的绝对动作、DROID 初始化、rank 16、完整 action projection、state token、融合模式头和 12,000 步预算，只改变连续 flow loss 的任务阶段权重；模式 CE 与模式头 CE 不加阶段权重。

冻结权重按 `[pregrasp, grasp_approach, lift, transport, place, release]` 排列，为 `[2.035714286, 2.035714286, 1.221428571, 0.407142857, 0.610714286, 0.407142857]`。它们由相对比例 `[5, 5, 3, 1, 1.5, 1]` 和训练集阶段计数 `[780, 809, 900, 2296, 786, 300]` 做总体频率归一化，5,871 帧上的期望 selected weight 为 `1.0`，不做 batch-local 归一化。预注册配置为 `configs/mobile_pi05_b3_sw_stage_weighted_flow_v1.json`；实现、合同、精确 checkpoint 审计和启动链在隔离目录通过 `28 passed`，尚未训练，不能计为能力结果。

Radeon 新持久化根目录为 `/workspace/persistence/parcel-sorter-opt-v1`。后续新 checkpoint 写入 `runs/`，日志与筛选结果写入 `outputs/`，小型合同与归档写入 `artifacts/`。正在运行的 LIBERO action-step screen 保持原路径直至完成，随后只归档合同、JSON 摘要和必要模型资产，避免复制全部历史视频和遥测。该 screen 的 10-step development control 已完成 `38/40`，但四臂选择尚未结束，此数值不得替代冻结的 400 回合确认成绩。

# 2026-07-29 LIBERO action-step 筛选完成与持久化开发配对

四臂 screen 在相同 40 个 development task/state 单元上完成，全部 return code、计时、显存和 ROCm 遥测门均通过。10-step control 为 `38/40`、634 次模型推理、暖态模型 P95 `528.58 ms`、`18.37 Wh`；4-step 为 `38/40`、1,589 次推理、`495.03 ms`、`35.70 Wh`；8-step 为 `40/40`、751 次推理、`632.84 ms`、`20.72 Wh`；6-step 为 `39/40`、1,040 次推理、`536.59 ms`、`25.33 Wh`。所有臂的峰值 allocated 显存均为 `8.965 GiB`。按预注册的成功率优先规则，8-step 是唯一进入完整开发集配对的候选；该 40 回合结果不是确认分数，也不能据此声称超过公开 PI0.5 或 PI0.6。

screen 的合同、逐臂 JSON/JSONL 和 `SCREEN_SUMMARY.json` 已归档到 `/workspace/persistence/parcel-sorter-opt-v1/artifacts/pi05-libero-action-steps-screen-v2`，摘要 SHA-256 为 `cbbef5d23379f5729b0f22cf333908ddaa73bf7f2b3b86ee00c778596c2ead22`。冻结的 `400+400` development 协议与哈希清单位于 `artifacts/pi05-libero-action-steps-protocol-v1`；最终 one-shot confirmation 协议在完整 development 结果可见前冻结于 `artifacts/pi05-libero-action-steps-confirmation-protocol-v1`。完整 development 配对于持久化 `outputs/pi05-libero-action-steps-development-v1` 启动，主 PID 为 `1109846`，先运行 10-step control，再运行 8-step candidate；只有候选在全部 400 个配对 development 单元上严格胜出，才允许打开确认集。

B3-SW 已从隔离 staging 部署到实际 Radeon 仓库。部署前后源码快照和哈希保存在 `/workspace/persistence/parcel-sorter-opt-v1/artifacts/mobile-pi05-b3-sw-deployment-v1`；实际仓库的 28 项相关回归和四个 shell 入口语法检查通过。B3-SW 训练尚未启动，必须等待 LIBERO development 配对释放 GPU；新 checkpoint 将写入持久化 `runs/`，预注册配置与关键源码哈希将在启动时写入持久化 `artifacts/`。
