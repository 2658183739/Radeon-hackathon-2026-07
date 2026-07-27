# PASH Primitive 学习与进度通道 SmolVLA

## 当前状态

本扩展把原来只有摘要的 PASH 技能写回候选，推进为可训练的 primitive 数据。代码已经完成，
并通过单张 Radeon 训练冒烟；它还没有通过冻结晋级 campaign，因此正式运行仍保留 v2 checkpoint。

| 能力 | 当前证据 |
| --- | --- |
| 事件式 primitive 切分 | 4,557/4,557 帧与只用于审计的阶段标签一致 |
| 可按 primitive 控制的数据集 | 7 个 episode、24 条任务文本、43 维状态、RGB、20 维动作 |
| 带进度通道的 SmolVLA 训练 | 单 Radeon/ROCm 完成 10 步 AMP 训练 |
| checkpoint 重载与 Harness 推理 | 一次有限 20 维预测，Harness 输出安全 19 维执行动作 |
| 闭环机理案例 | 一个小纸箱任务完成，放置误差 1.28 cm |
| 任务提升或泛化 | 冒烟与单次闭环案例均不能证明 |

## 方法

PASH 现在有三个自适应时间尺度：

1. **单次 rollout 内：**Force Memory 与 Harness 候选门收紧或撤销学习权限，不修改权重；
2. **最多三次尝试间：**第一个失败 primitive 结合任务记忆和全局记忆选择恢复策略；
3. **数据 campaign 间：**成功轨迹切分并改写任务文本，在 Radeon 上离线再训练，然后由冻结配对
   评估决定晋级或保留旧 checkpoint。

切分器不读取 `observation.stage_id`，也不读取快递真值位姿。它只使用两段持续底盘运动与左侧
三吸盘的吸附、释放命令：

```text
静止 -> 底盘接近 -> 吸附 -> 抬升 -> 带载运输 -> 放置 -> 释放 -> 后撤
```

由此恢复 `pregrasp`、`grasp_approach`、`lift`、`transport`、`place` 和 `release` 六个连续
primitive。阶段标签只在切分后用于独立一致性审计。

每段轨迹得到自己的语言指令，同时保留原始分类搬运任务。19 维控制动作后追加从 0 到 1 的
primitive 进度监督。模型的第 20 维只作为遥测和未来完成提示，只有前 19 维能够进入 Harness；
因此它不能绕过 35 N 门、工具互锁、双臂刚体投影、IK 或确定性安全快环。

## 自动自我改进流程

在已有可恢复周期上增加 `--primitive-learning`：

```bash
cd /workspace/parcel-sorter-opt-v1
source /workspace/rdna/bin/activate
python scripts/run_mobile_self_improvement_cycle_rocm.py \
  --cycle-id primitive-v1 \
  --cycle-dir outputs/mobile-self-improvement-primitive-v1 \
  --source-campaign-audit outputs/source-frozen-holdout-v2-audit.json \
  --base-training-config configs/mobile_suction_collection_v1.json \
  --baseline-checkpoint outputs/train/mobile-smolvla-mass-aware-b8w4-2400step-v2/checkpoints/002400/pretrained_model \
  --holdout-trials 100 --holdout-seed 20260728 \
  --training-steps 2800 --batch-size 8 --num-workers 4 \
  --policy-hz 3 --evaluation-workers 4 --primitive-learning
```

该模式会在 Radeon 训练前自动插入 `build_primitive_dataset` 和
`audit_primitive_dataset`，并选择 20 维动作契约。原有基线/候选隔离、Wilson 不劣性、零力
越界、单卡 ROCm 和回滚门保持不变。机器人运动过程中不会修改权重。

## Radeon 冒烟证据

源课程包含 7 个 episode、4,557 帧 RGB-D。事件切分器生成四类快递乘六阶段共 24 条任务文本，
并与 4,557 帧阶段审计标签逐帧一致。数据审计确认 43/20 张量有限、四元数单位化、工具命令为
二值、深度为米制、策略输入没有特权位姿，进度严格位于 `[0,1]`。

SmolVLA 共加载 450,061,536 个参数，训练其中 99,896,352 个参数；在单张 `gfx1100` Radeon、
ROCm 7.2.1 上完成 10 步 AMP 并保存 checkpoint。模型 SHA-256 为
`86635367299d0ba1c30af4130138fffabc4dfe6bbe6adc8785f7f93ef9fcdb58`。随后一次冷启动重载
产生有限控制与进度值，Harness 继续只输出 19 维执行动作。冷启动延迟不作为性能结论。

证据文件位于：

- `evidence/training/pash-primitive-dataset-v2-manifest.json`
- `evidence/training/pash-primitive-dataset-v2-audit.json`
- `evidence/training/pash-primitive-smolvla-rocm-smoke-v1.json`
- `evidence/training/pash-primitive-smolvla-single-inference-rocm-v1.json`
- `evidence/training/pash-primitive-smolvla-rocm-smoke-v1.log`

## 闭环机理结果

随后在同一张 Radeon 上，把 10 步进度通道 checkpoint 加载到未放宽门限的 Genesis Harness
闭环。一个确定性 `small_carton` 开发案例完成抓取、运输、放置与释放，最终误差为 1.28 cm。
吸盘吸附 1 次、断吸 0 次，接触峰值 7.93 N、吸附力峰值 11.84 N。SmolVLA 共调用 79 次，
热态平均/P95 延迟为 201.67/210.05 ms。Harness 完整回退 2 次、紧急停止 0 次；学习式底盘
残差实际作用 3,578 个物理步，同时确定性的运输截止时间接管仍保留最高权限。

压缩证据位于 `evidence/mobile_bimanual/primitive_learning_v1/summary.json`。这只是一个开发
机理案例，不构成成功率、收敛性、primitive 完成度准确率、未见物体泛化或相对保留 v2
checkpoint 的晋级结论。

## 失败与修复记录

第一版数据把任务文本写成普通 parquet 列，而 LeRobot v3 要求任务文本是具名 pandas 索引，
因此训练在第一个 batch 前以 `Task cannot be None` 停止。构建器随后按 LeRobot 原生契约重写，
v2 数据经实际 `LeRobotDataset` 取样确认任务非空且动作为 20 维，第二次训练完成。失败运行不计入
训练证据。

## 论文来源与声明边界

Harness VLA 启发了学习原语、确定性动作、记忆与重试调度的分离
（[项目页](https://harnessvla.github.io/)、[论文](https://arxiv.org/abs/2607.08448)）。
InSight 启发了 primitive 重标注、进度通道、缺口获取与离线写回：Maggie Wang、Lars Osterberg、
Stephen Tian、Ola Shorinwa、Jiajun Wu、Mac Schwager，*InSight: Self-Guided Skill Acquisition
via Steerable VLAs*，[arXiv:2606.24884](https://arxiv.org/abs/2606.24884)，DOI
`10.48550/arXiv.2606.24884`。

元数据于 2026-07-27 通过 OpenAlex `/works` 精确标题检索核验，返回 arXiv 编号、DOI、作者、
日期与 CC-BY 开放记录。arXiv Atom 标题检索当时超时，因此正式文档引用已解析的 arXiv 原始记录，
不引用公众号二手文章代替论文。

本实现是面向三吸盘、V 型托架、移动双 Franka 仿真的原创 PASH 适配，没有复制 Harness VLA 或
InSight 代码。当前 10 步证据只证明接线，不证明收敛、任务提升、未见物体泛化、VLM 自主发现缺口
或 Sim-to-Real。
