# PI0.5 快递搬运研究流程纠错协议

状态：训练暂停。只有本协议中的前置门全部通过后，候选训练才允许启动。

## 1. 已确认的流程错误

旧离线筛选固定使用数据索引 `0, 644, 1286, 3636, 4699, 5285`。这些样本都是训练集轨迹的首帧，且全部属于 `pregrasp`。因此旧结果只能说明训练分布上的抓取模式路由，不能说明六阶段动作学会，更不能作为检查点晋级或闭环成功证据。

旧 B0 记录中的 `action_fidelity_error_count=0` 也不成立：当时没有执行动作保真评测。该字段已改为 `null`，状态改为 `routing_only_action_fidelity_not_evaluated`。

## 2. 两个不可混用的面板

### tiny_overfit_contract

- 来源：训练数据的显式小子集。
- 覆盖：顶部吸附、侧面吸附、协同托举 × `pregrasp`、`grasp_approach`、`lift`、`transport`、`place`、`release`。
- 用途：只验证归一化、动作解码、完整动作投影和训练链能够学习。
- 禁止声明：泛化、真实闭环成功、排行榜优势。

### heldout_action_development

- 来源：至少每种抓法两个独立、未进入训练的数据来源。
- 要求：每个观察都有完整动作标签，并明确标记 `do_not_train`。
- 用途：检查点选择和接触标定后的分阶段动作阈值评测。
- 禁止声明：冻结测试集成绩或最终论文结果。

现有 held-out 观察只有 `pregrasp` 首帧且没有动作标签，只保留为路由诊断，不能升级为该面板。

## 3. 固定执行顺序

1. 数据合同审计：特征、动作语义、归一化、来源身份和重复回放。
2. 两步 smoke：只验证 ROCm 前向、反向、保存和加载；不得晋级。
3. tiny diverse overfit：18 个模式/阶段单元全部通过，路由、动作、结构错误均为 0。
4. 独立开发动作筛选：使用接触标定后的分阶段阈值，三个错误计数均为 0。
5. 纯 VLA `3/3` 闭环开发门：禁止专家动作、回退和低于 1.0 的动作缩放计入成功。
6. 开发 benchmark：只用于调参和消融选择。
7. 冻结 confirmation：一次性运行，不能按结果补跑或改阈值。
8. AMD 推理优化：仅在模型冻结后比较延迟、显存、能耗、温度和长稳，不改变任务成功定义。

任何一步失败都返回上一层定位原因，不允许跳到更大训练或最终评测。

## 4. 门禁文件

- `build_mobile_pi05_stage_panel.py` 从 LeRobot Parquet 和数据来源清单生成冻结面板。
- `audit_mobile_pi05_training_launch.py` 在训练进程创建前检查训练角色、来源数量、scheduler 和 tiny-overfit 证据。
- `probe_mobile_pi05_checkpoint_rocm.py` 只接受冻结面板，不再接受手写索引。
- `probe_mobile_pi05_high_noise_mode_rocm.py` 也绑定同一冻结面板、数据清单和 episode，不允许把旧六帧重新包装成诊断证据。
- `summarize_mobile_pi05_mode_screen.py` 强制读取面板和分阶段阈值。
- `write_mobile_pi05_tiny_overfit_gate.py` 只有在 18 个单元的三类错误均为 0 时写出晋级门。
- `select_mobile_pi05_route_checkpoint.py` 只选择通过独立开发动作筛选的最早检查点，路由-only 结果直接拒绝。
- `audit_mobile_pi05_resume_training.py` 要求恢复前后合同哈希完全一致，并核验原始和拟议 launch audit；断点续训不得改变数据、scheduler、batch、投影或损失权重。

所有面板、阈值、合同、检查点和门禁均使用 SHA-256 绑定。缺文件、缺动作、错角色、来源重叠、指纹变化或指标缺失都按失败处理，不推断为 0。

## 5. 分阶段阈值

动作阈值必须分别覆盖六个阶段，包含位置、姿态、底盘速度、任务进度和工具命令。开发阈值只有在至少两条独立成功接触轨迹上完成标定后，才可标记为 `deployment_calibrated=true`。当前尚无满足条件的标定证据，因此不能创建“已校准”的开发阈值文件，也不能选择新候选。

## 6. 失败分类

失败标签记录首个因果门：

- `scene_stability_failure`
- `contact_failure`
- `suction_latch_failure`
- `lift_support_failure`
- `transport_failure`
- `placement_failure`
- `release_failure`
- `force_safety_abort`

没有接触或没有吸附锁定时，绝不能记录为 `lift_success`。旧名称仍可用于读取历史文件，但新采集结果只写上述失败标签。

## 7. 当前可声明结论

截至本协议落地时，B0 与 B1 的严格纯 VLA 闭环均为 `0/3`，未形成有效吸附锁定。B3-SW 的离线动作错误从 B1 的 22、B2 的 17 下降到 14，但仍未通过动作门，且该面板不是独立的阶段完整开发集。现阶段只能声明“发现并修复了评测流程泄漏，候选训练尚未获准启动”，不能声明已经超过 π0.5、π0.6 或任何排行榜模型。
