# π0.5 VLA 快递抓取研究协议

## 方法身份与声明边界

本项目的最终学习方法是 π0.5 VLA。确定性模块只负责坐标变换、表面法向姿态、IK、碰撞检查、35 N 安全中止和释放互锁；它不能替代 π0.5 的抓取模式判断、接触点纠偏、失败恢复、primitive 进度判断或运输残差，也不能用确定性专家成功率冒充 VLA 成功率。

2026-07-27 的严格三模式筛选使用 1,000 步 π0.5 checkpoint、RGB-D、`pi05_residual` 闭环和 VLA goal verdict，在 `micro_box`、`small_carton`、`flat_mailer`、`upright_canister`、`large_mailing_tube` 上得到 0/5。模型在所有回合预测 `top_suction`，最大接触残差约为 `1e-8 m`，等同零输出。该 checkpoint 只作为种子基线，不构成已学会抓取或恢复的证据。

最低工程晋级点估计为冻结 105 回合至少 95 次完整抓取、运输和指定位置释放，即 `95/105 = 90.48%`。但 95/105 的 Wilson 95% 区间下界只有 83.35%，不能证明总体成功概率超过 90%。论文若要在单侧精确二项检验 `H0: p <= 0.90`、`alpha=0.05` 下声明“成功概率超过 90%”，同一 105 回合中必须至少成功 100 次；100/105 的单侧 Clopper--Pearson 95% 下界为 90.25%。在正式冻结评测达到相应结果前，不作该声明。

## 可学习合同

数据合同向 π0.5 batch 提供顶部 RGB-D、43 维机器人状态、三吸盘密封状态、包裹形状/尺寸/质量、重试次数、任务阶段、双臂短时力历史和双臂名义接触锚点，抓取模式 one-hot 在所有阶段固定隐藏。需要特别区分“batch 中存在”与“模型实际消费”：LeRobot 0.6.1 当前 π0.5 主干只读取图像和语言，因此 R6--R9 通过模式盲语言桥消费形状、尺寸、质量、阶段和重试次数，尚未消费逐杯密封、力历史或其余状态。后续 E4 将以可保存的原生状态 token 接入这些通道，并把腕部 RGB-D 作为独立扩展，不与 E3 同时引入。

π0.5 输出为 14 维受约束动作：3 维底盘速度残差、左右臂各 3 维接触点残差、三模式 logits、吸盘意图和 primitive 进度。模型在 `pregrasp`、`grasp_approach`、`lift`、`transport` 获得有限执行权；姿态、关节求解和最终释放由安全层锁定。

一次物理成功只有在以下条件全部满足时才计入 VLA 成绩：checkpoint 实际加载；所有关键阶段发生 π0.5 推理；禁用专家接管或单独报告回退；抓取、抬升、运输、放置和释放全部完成；位置误差不超过 4 cm；吸附力、接触力和托架力均低于 35 N。零残差简单回合可以是正确策略，但整个评测组必须报告非零动作分布，并通过关闭/打乱 VLA 输出的配对消融证明模型贡献。

## 验证式自进化数据

现有 4,557 帧种子数据只有模式、吸盘意图、进度和零残差监督，无法训练接触恢复。旧恢复课程固定随机种子 20260727，从 21 类开发配置生成 315 个毫米级接触锚点偏差回合；它可作为专家课程预训练，但不能证明 π0.5 自主恢复。正式自进化数据改为直接记录 π0.5 在 Harness 前实际输出的 14 维 residual、对应 80 维可观测状态、RGB-D、模式 logits、chunk 索引和推理/保持标记，不再由事后 recovery offset 反推模型标签。

失败回合只进入 failure replay，不能直接作为正确动作示范。只有完成抓取、运输、指定位置放置、释放，且 VLA 自主选择模式、VLA 确认目标到达、专家回退为 0、紧急停止为 0、无力违规并包含非平凡 residual 的轨迹才能提交 LeRobot episode。所有其他回合清空行为克隆缓冲区，只保存失败原因。训练、开发和冻结评测 episode ID 必须无交集。模型权重只在回合之间离线更新，不在同一 rollout 中在线改变。

第一轮先收集三种模式各至少两个成功非零恢复回合，验证 80 维状态、14 维动作、锚点反推和非零标签。通过后扩展到 300–500 条成功轨迹；未达到成功数量时不靠复制帧或失败轨迹凑数。

## 训练与晋级

基础模型固定为 `lerobot/pi05_base` 对应已缓存 revision。LoRA 使用 rank 16、alpha 32，冻结视觉编码器，bfloat16 AMP，先做 1,000 步接线检查，再比较 3,000、6,000 和 10,000 步 checkpoint。离线 loss 只用于排错，不作为机器人能力证据。

候选必须在同一冻结 105 回合上与基线配对。独立实验单位是一个唯一冻结快递 episode；episode 内的视频帧、扩散采样、三次路由投票、控制时刻和失败重试都是重复测量，不能扩充样本量。主指标为任务成功率及 Wilson 95% 区间；配对成功/失败使用 exact McNemar 检验。同时报告力违规率、稳定密封率、位置误差、各阶段失败率、π0.5 延迟、非零残差比例和专家回退次数。候选达到至少 95/105、力违规不增加、数据隔离通过且 checkpoint/hash 完整时获得工程晋级；只有至少 100/105 且通过单侧精确二项门时，才支持总体成功概率超过 90% 的确认性表述。

## 消融矩阵

| ID | 设置 | 作用 |
| --- | --- | --- |
| E0 | 统一传感频率的确定性 Harness | 物理执行对照，不是主方法 |
| E1 | π0.5 RGB 零残差种子 | 证明仅增加 VLA 名称或训练步数无效 |
| E2 | E1 + 三模式均衡语言/状态监督 | 检验模式路由学习 |
| E3 | E2 + 验证成功的非零接触恢复 | 检验接触点 VLA 纠偏 |
| E4 | E3 + RGB-D、逐杯密封和力历史 | 检验接触可观测性 |
| E5 | E4 + 验证式失败 replay 与再训练 | 检验自进化闭环 |

补充机制消融包括：打乱 π0.5 输出、关闭接触残差、关闭力历史、关闭第三次模式切换、关闭 Harness 候选验证。任何消融组都共享同一姿态/IK/力安全层和传感采样频率。

## 两条投稿线

Workshop 线对应 IROS 2026 Workshop **Physical World Models for Scaling Embodied AI**。官方范围明确包含 Physical World Models as Data Engines、World Action Models for Embodied Decision-Making、视觉-触觉接触操作、预测式安全动作选择和自改进 agents。投稿为 4–8 页（不含参考文献）、IROS workshop 模板、双盲、非归档；截稿 2026-08-10，录用通知 2026-08-20，camera-ready 2026-09-20，海报展示 2026-10-01，部分论文口头 spotlight。

Workshop 稿优先写成可复现的技术/负结果论文：零残差 π0.5 为什么失败，验证式恢复数据如何产生，以及 E1–E5 的闭环结果。官方页面为 <https://physical-world-models.github.io/IROS2026/>，OpenReview 为 <https://openreview.net/group?id=IEEE.org/IROS/2026/Workshop/PWMS>。IROS 2026 官方作者资源提供 [LaTeX 模板](https://ras.papercept.net/conferences/support/tex.php) 和 [Word 模板](https://ras.papercept.net/conferences/support/word.php)。

SCI 三区线在冻结评测超过 90%、多 seed 和公开数据集实验完成后再定稿。该稿扩展统计、泛化、公开基准适配和更完整消融，不提前复用 Workshop 的同一实验结论作重复发表。Workshop 为非归档减少了后续扩展投稿冲突，但最终仍需逐刊核对重复内容政策。

## 当前可复现入口

- 端到端学习指南：`docs/PI05_VLA_END_TO_END_GUIDE_CN.md`
- 非零标签合同：`src/parcel_sorter/mobile_pi05_contract.py`
- 恢复课程生成：`scripts/build_mobile_pi05_recovery_curriculum.py`
- 成功轨迹采集：`scripts/collect_mobile_suction_dataset_rocm.py`
- π0.5 数据转换：`scripts/build_mobile_pi05_residual_dataset.py`
- π0.5 自主 residual 记录：`src/parcel_sorter/mobile_pi05_dataset.py`
- π0.5 LoRA：`scripts/train_mobile_pi05_rocm.sh`
- 闭环执行与证据：`scripts/evaluate_mobile_suction_lift_rocm.py`

所有开发失败、参数变化、训练日志、checkpoint hash、冻结清单和负结果都保留。论文表格只能从机器生成的 summary/audit 读取，不能手工修改成功数。

冻结样本量的先验功效记录为 `evidence/pi05_vla/pi05-success-power-plan.json`。在 105 回合和单侧 `alpha=0.05` 下，真实成功率为 95% 时拒绝 `p <= 0.90` 的功效仅为 57.11%；真实成功率为 97% 时功效为 90.33%。若真实成功率约为 95%，达到 80% 和 90% 功效分别需要约 179 和 239 个独立 episode。因此 105 回合适合作为工程晋级与 workshop 主实验，但 SCI 确认性版本应扩展独立冻结 episode 数或明确把结论限制为点估计与区间估计。
