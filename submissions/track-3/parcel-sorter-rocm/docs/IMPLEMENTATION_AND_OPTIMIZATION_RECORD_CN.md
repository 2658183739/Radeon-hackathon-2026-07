# 实施与优化学习记录

### 2026-07-25：冻结实验战役协议

当前主要风险是比较不可比，而不是继续盲目增加未经验证的控制参数。
因此新增 `configs/campaign_v1.toml` 和 `src/parcel_sorter/campaign.py`。
校验器会拒绝非 ROCm 设备、多 GPU、不是 35 N 的安全上限、重复回合编号、
缺失随机种子、未声明开源许可的模型以及不完整的验收门槛。目录哈希已经
写入；均衡数据分片完成前，数据集和拆分哈希明确保留为 `PENDING`，不会把
计划伪装成结果。

同一模块增加了按 `box`、`upright_cylinder`、`horizontal_cylinder` 以及末端
执行器处理类别的交叉汇总。类别报告与总体成功率分开，避免总体数字掩盖某
一类物理对象失败或使用了未支持夹具。

目标 Radeon 环境已验证：127 项测试和 6 个子测试全部通过。协议指纹为
`edb3e171b6e68989f70dab9641792659c8a3cba5e50837c872fe3a120681db6f`。

英文配套文档：[IMPLEMENTATION_AND_OPTIMIZATION_RECORD.md](IMPLEMENTATION_AND_OPTIMIZATION_RECORD.md)

## 用途与边界

这份学习记录描述可观察的工程证据、模块职责、备选方案、决策、验证和下一步实验。它不展示
私有逐字思维链，也不把计划写成已经实现的结果。

项目遵循可复现机器人学习与机器学习工程的通行做法：配置即代码、不可变的数据和评测清单、
先写契约再实现、一次实验只改一个主变量、产物哈希、留出集闭环评测，以及独立于学习策略的
确定性安全层。

| 状态 | 含义 | 允许的表述 |
| --- | --- | --- |
| 已验证 | 在记录的 Radeon 环境中重复执行 | “已在 Radeon 上验证” |
| 链路烟雾 | 接口可以执行，但任务质量尚未证明 | “链路烟雾已完成” |
| 计划 / 门禁 | 尚未实现，或被明确前置条件阻塞 | “计划中”或“兼容性门禁中” |

## 系统能力图

| 层级 | 代码职责 | 当前状态 | 重要边界 |
| --- | --- | --- | --- |
| 实验契约 | `config.py`、TOML 目录、`contracts.py` | 已验证 | 非法范围和不支持的末端执行器会提前失败 |
| 回合生成 | `randomization.py`、`episode_plan.py` | 已验证 | 稳定种子和 profile 命名空间避免审计冲突 |
| 物理与传感器 | `genesis_env.py` | 已验证 | Genesis、Panda、Box/Cylinder、RGB-D、本体状态、接触力 |
| 专家与监督器 | `expert.py`、`state_machine.py`、`runner.py` | 专家基线已验证 | IK/PD 与 35 N 安全边界始终在模型外 |
| 数据完整性 | `dataset.py`、`data_quality.py`、`dataset_split.py` | 已验证 | 仅成功回合进入 LeRobot；RGB-D 深度必须是米制 |
| 新增采集规划 | `collection_plan.py`、`plan_balanced_collection.py` | 已实现，待 Radeon 实跑 | 历史记录只估计预算，不抵扣新分片配额 |
| 模仿学习 | `train_act_rocm.sh`、LeRobot ACT | 链路烟雾 | 当前 190 个成功回合尚未通过均衡数据门禁 |
| Diffusion | `train_diffusion_rocm.sh` | 单步烟雾 | 尚无匹配的闭环能力结论 |
| VLA / ROS 2 | 兼容性脚本与研究矩阵 | 门禁中 / 计划中 | 许可证、ROCm 算子、数据和闭环门禁仍未通过 |
| Radeon 执行 | 预检、安装、基准与矩阵脚本 | 基础栈已验证 | 必须是单张 AMD Radeon 与 ROCm HIP |

## 工程过程与决策

### 1. 采用分层机器人系统，而不是让一个大模型包办全部

**决策。** Genesis + Franka Panda 负责物理和执行；确定性状态机负责任务阶段与安全；ACT
作为轻量学习基线。策略输出八维笛卡尔动作，有限值检查、四元数归一化、笛卡尔限幅、IK、PD、
夹爪阶段控制和 35 N 中止仍放在模型外。

**原因。** 即使学习策略尚未稳定，接触处理、运动限幅和失败恢复仍可独立测试。

**验证。** 专家轨迹、ACT 训练/保存/加载和学习策略闭环接口已在单张 Radeon 上执行。固定
留出集匹配评测完成前，学习任务能力仍只能称为链路烟雾。

### 2. 先修复仿真正确性，再调控制器

**观察。** 横向圆柱曾出现半径和出生高度不一致，早期夹爪姿态也沿错误方向闭合。

**决策与原因。** 先修复 primitive 尺寸、由半径推导的放置高度和手指轴向，再修改控制增益
或安全阈值。围绕错误几何调出的控制器会产生误导性结果。

**验证。** 几何和目录测试覆盖 Box/Cylinder 映射。因果证据和被拒绝候选保留在
`OPTIMIZATION_SESSION_2026-07-25.md`。

### 3. 把局部优化限制在局部失败模式中

**观察。** 全局三帧稳定接触改善了一个邮筒案例，却让多个箱体 profile 回归。

**决策与原因。** 全局保持一帧，三帧只用于圆筒 profile。滚动摩擦和材料改动也遵循同样
原则，使一个物体类别不会悄悄改变其他物体的基线。

**验证。** 目录回归恢复到 8/12 的诊断完成模式。它只是回归烟雾，绝不是成功率结论。

### 4. 加入多模态学习前先修复数据语义

**观察。** 历史深度缩放错误，其米制中位数不合理。

**决策。** 保留历史 RGB/状态数据用于复现，拒绝将其用于 RGB-D；新分片保存原始 float32
米制深度和确定性深度可视化。

**原因与验证。** 静默转换旧数据无法审计。`data_quality.py` 在 RGB-D 训练前检查形状、
元数据、米制单位和合理深度统计。

### 5. 比较模型之前冻结数据与评测

**决策。** 按 profile 分层的清单将原始审计 ID 映射到 LeRobot 成功回合 ID。ACT 和
Diffusion 使用同一份训练/验证/留出列表；检查点比较也要求 episode 集和安全阈值一致。

**原因。** 不同拆分、episode 或安全阈值会让模型排序失去意义；总体成功率也可能掩盖困难
profile 的失败。

**验证。** 拆分和比较代码会拒绝未完成采集、泄漏、不匹配证据和不支持的模式，同时报告
逐 profile 结果、Wilson 区间、掉落、接触力和延迟。

### 6. 本轮决策：采集干净的新均衡分片

**证据。** 已完成的 Radeon 采集包含 400 个审计回合，但只有 190 个成功回合进入 LeRobot。
数据类别不均衡，且未达到正式数据门禁。

**备选方案。** 立即训练；向旧 LeRobot 数据集追加；或根据审计历史创建干净的均衡分片。

**决策。** 创建一个独立新数据集：12 个训练 profile 各 30 个成功 RGB-D 回合，共 360 个。
历史记录只用于估计工作量，不抵扣新目标。当前 writer 有意避免改变顺序和来源的危险追加语义。

**代码能力。** `plan_balanced_collection.py` 对 `audit_dataset/episodes.jsonl` 计算指纹、
逐 profile 统计并写出有版本的计划。`run_expert.py --collection-plan` 在一个干净 writer
会话中执行冻结后的不同 profile 预算。

**规划算法。**

```text
Wilson 下界       = 历史成功率的保守 95% 置信下界
规划成功率         = max(Wilson 下界, 配置的规划成功率下限)
建议尝试回合数     = ceil(新数据集目标成功数 / 规划成功率 * 过采样系数)
```

成功率下限用于在历史成功为零时避免产生无限计划；它只是资源调度保护，**不是**成功保证。当
Wilson 下界低于就绪阈值时，profile 被标记为 `requires_expert_diagnostic`。批量采集默认
拒绝这种计划，只有明确标记为诊断运行时才能显式确认。

**原因。** 当前最大的限制是低质量、不均衡的专家数据，而不是模型大小。该机制避免在
`large_narrow_carton`、`mailing_tube`、`upright_canister`、`medium_carton` 等困难类别尚未
解决时继续收集低质量数据。

**验证。** 单元测试覆盖保守规划、新分片目标、未就绪计划拒绝、显式确认、不同 profile
预算、重复 profile 拒绝和确定性命名空间。真正的 Radeon 执行仍需完成后才能成为结果。

### 7. 调控制器前增加轨迹级失败归因

**问题：**第一个控制器改动应该是什么，究竟哪个阶段在产生不安全的专家数据？

**可观察实现：**`failure_analysis.py` 把每条已完成轨迹转换为一个主要结果，保留第一次力违规的
上下文，并聚合任务、安全、阶段到达、接触力和 profile 统计。`analyze_expert_failures.py` 在派生
JSON 中记录源 summary 的路径、大小和 SHA-256。测试覆盖力上下文、非力失败、缺失轨迹和非法安全阈值。

**Radeon 结果：**400 次尝试、190 次成功、161 次力违规。接近阶段占 104 次，初始状态已有 22 次。
派生证据为 `evidence/expert/radeon-dataset-400-v2-failure-analysis.json`。

**决策：**下一次只改安全初始化与尺寸感知接近。在困难专家 profile 通过诊断前，不执行规划中的
1,775 次采集；也不把因素中位数解释成因果效应。

**验证：**专项测试和完整 86 项测试均在 ROCm 环境通过。失败分析已经验证；控制器改动仍是计划状态，
必须等匹配的 Radeon A/B 完成后才能声称有效。

## 立即在 Radeon 上执行的流程

在项目根目录运行。激活脚本先寻找项目 `.venv`，之后才尝试旧云端路径；不要假定
`/workspace/rdna` 一定存在。

```bash
cd /workspace/parcel-sorter-opt-v1
source scripts/activate_radeon_env.sh
export PYTHONPATH="$PWD/src"

python -m unittest discover -s tests -q

python scripts/plan_balanced_collection.py \
  --config configs/catalog_v2.toml \
  --audit-manifest outputs/radeon-dataset-400-v2/expert/audit_dataset/episodes.jsonl \
  --output outputs/radeon-balanced-v3/collection-plan.json
```

读取计划中的 `summary.blocked_profiles`。对每个被阻塞 profile，只改一个控制或物理变量后
做短小、隔离的专家诊断。诊断分片不用于训练时，不要传 `--lerobot`。

```bash
python scripts/run_expert.py \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --episodes 10 \
  --start-episode 5000 \
  --profile mailing_tube \
  --record-sensors \
  --output outputs/diagnostics/mailing-tube-v1
```

专家诊断通过所选门禁后，重新生成计划。只有此时才启动新的均衡训练分片：

```bash
python scripts/run_expert.py \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --collection-plan outputs/radeon-balanced-v3/collection-plan.json \
  --record-sensors --lerobot \
  --output outputs/radeon-balanced-v3

python scripts/audit_dataset.py \
  --dataset-root outputs/radeon-balanced-v3/expert/lerobot_dataset \
  --require-depth-rgb

python scripts/build_dataset_split.py \
  --audit-root outputs/radeon-balanced-v3/expert/audit_dataset \
  --dataset-root outputs/radeon-balanced-v3/expert/lerobot_dataset \
  --output outputs/radeon-balanced-v3/dataset-split.json \
  --seed 20260725
```

完整采集命令故意没有加入 `--allow-unready-collection`。它是给标记诊断运行的确认开关，
不是正常绕过数据质量的方式。

## 按优先级排序的优化计划

| 优先级 | 假设 / 改动 | 固定条件 | 验收规则 | 不要做 |
| --- | --- | --- | --- | --- |
| P0 | 按阶段、几何、摩擦和接触轨迹诊断高力专家失败 | 相同 profile、episode ID、35 N | 力中止下降，成功率和吞吐不下降 | 提高安全阈值 |
| P0 | 生成新的 12 类均衡 RGB-D 分片 | 独立输出根目录和冻结目录 | 每个训练 profile 至少 30 个成功回合 | 含糊地追加旧数据 |
| P1 | ACT RGB 与 RGB-D late fusion 对照 | 同一拆分、种子 11/22/33、预算 | 留出集任务更好且安全/延迟不退化 | 用不同拆分比较 |
| P1 | 轻量 Diffusion 与 ACT 对照 | 相同数据、安全包装和留出 episode | profile 宏平均更好且 P95 可用 | 把单步烟雾当能力 |
| P1 | 课程随机化和困难样本聚合 | 全范围留出基准固定 | 全范围表现提升 | 缩窄基准 |
| P2 | 对渲染、转换、传输、推理、IK、物理分别分析 | 同步计时、单 GPU | 端到端至少 15% 提升且任务不退化 | 把入队时间当延迟 |
| P2 | AMP / BF16 / `torch.compile` 矩阵 | 相同模型、数据、评测 | 无 NaN，安全一致，记录内存和速度 | 同时改精度和架构 |
| P3 | VLA-Adapter 高层路由 | 许可证和 ROCm 算子审计 | 指令价值可测，ACT/安全层控制连续动作 | 用 VLA 替换安全控制器 |
| P3 | 吸盘、cradle、点云、ROS 2 | 有版本的硬件/控制契约 | 工具专属闭环安全报告 | 声明未实现硬件已支持 |

## 如何记录下一次改动

每一项实质改动都在开发日志和决策日志中新增一对中英文记录。原始 JSON、CSV 和日志放在
`evidence/` 或新的输出目录。

```text
编号与日期：
问题与失败证据：
基线提交、配置、运行时、清单哈希和 episode ID：
唯一主变量与被拒绝的替代方案：
新增或修改的代码契约：
任务、安全、性能和不确定性指标：
精确命令与产物路径：
决策：保留 / 拒绝 / 暂缓：
原因与重新评估条件：
```

本记录、配套的[工程流程与学习手册](ENGINEERING_PLAYBOOK_CN.md)和原始证据共同构成项目
事实来源。报告和视频应该引用结果状态与产物，而不是用不可复现的叙述替代证据。
