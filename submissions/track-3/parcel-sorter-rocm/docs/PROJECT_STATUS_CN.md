# 项目状态与复现协议

状态日期：2026-07-25。这是赛道三提交项目的短版操作视图。文档把已验证证据与计划中的
工作分开，避免把实验计划误写成已有能力。

## 当前 Radeon 运行状态

截至 2026-07-25，Radeon 专家采集已完成 400 个可审计回合。严格的 LeRobot 成功数据集包含
190 个回合，并被确定性拆分为 123 个训练回合、24 个验证回合和 43 个最终留出回合。ROCm 预检
通过后，基于此清单的 5,000 步 ACT RGB/RGB-D smoke 矩阵已启动；训练器对第一个 RGB seed 明确
记录 `cfg.steps=5000`。

这**不表示**已经通过“至少 300 个按 profile 均衡的成功 RGB-D 回合”的正式数据门禁。当前矩阵
只验证训练、checkpoint 和编排接线。正式 30K 模型比较与留出集闭环排名仍被阻断，直到补齐均衡
采集、通过相同审计，并冻结新的拆分清单。

同一张 Radeon 已对完成的 400 回合审计清单运行 `plan_balanced_collection.py`。它为新的独立
分片设定了更严格的目标：12 个训练 profile 每类 30 个成功回合，共 360 个；按当前保守成功统计
估计需要尝试 1,775 个回合。九个 profile 被显式阻塞，必须先做专家诊断：`book_box`、
`medium_carton`、`shoe_box_proxy`、`long_carton`、`large_narrow_carton`、`upright_canister`、
`mailing_tube`、`near_limit_box` 和 `electronics_box`。这是规划产物，不是新的数据或模型结果。

## 硬性约束

- 只使用一张 AMD Radeon GPU，并确保进程只看到一个设备；PyTorch 必须走 ROCm/HIP。
- 仿真器、代码、模型实现和数据必须开源或具备可审计的合法使用许可。
- 竞赛路径中的物理仿真、渲染、训练、推理和 benchmark 均在同一张 Radeon 上完成。
- 所有模型比较都要在选模前固定数据拆分、episode 编号、安全阈值、随机种子和产物哈希。

## 能力台账

| 领域 | 当前状态 | 证据或边界 |
| --- | --- | --- |
| 物理仿真 | 已验证 | Genesis + Franka Panda + Box/Cylinder + 两个分拣格口 |
| 传感器 | 已验证 | RGB、米制深度、深度 RGB 视图、关节、末端位姿、目标、接触力 |
| 专家控制 | 已验证为基线 | IK/PD、夹爪斜坡、接触确认、重试、释放检查、35 N 中止 |
| 闭环 | 专家路径已验证 | 检测 -> 接近 -> 抓取 -> 抬升 -> 搬运 -> 释放 -> 恢复 |
| RGB ACT | 已集成并通过烟雾 | 训练/保存/加载/评测适配器均可用；未通过留出集前不提升为正式成功率 |
| RGB-D ACT | 已集成并通过烟雾 | 修正后的米制深度分片通过审计；单步闭环只证明接口 |
| 轻量 Diffusion | Radeon 单步烟雾 | 完整匹配训练和闭环比较待做 |
| 鲁棒性统计 | 已实现 | 分 profile 指标和 Wilson 95% 区间；零重试样本标记为未知 |
| 均衡采集规划 | 已实现并完成 Radeon 检查 | 新数据集 360 个成功目标、配置/审计指纹、不同 profile 预算和专家诊断门禁 |
| 行业大箱 | 仅评测 profile | 当前平行夹爪不能宣称具备吸盘处理能力 |
| 圆柱快递 | 部分/未解决 | 已有作用域滚动物理和接触控制；仍需要 cradle 末端执行器 |
| VLA | 不在结果主线 | VLA-Adapter 仍是许可证与 ROCm 兼容性试验 |
| ROS 2 / 云服务 | 尚未实现 | 等仿真器—策略契约稳定后再加入 |

## 推荐执行顺序

```text
1. preflight_radeon.sh
2. 缺依赖时执行 bootstrap_radeon.sh
3. python -m unittest discover -s tests -q
4. run_expert.py --config configs/catalog_v2.toml --record-sensors --lerobot
5. audit_dataset.py --require-depth-rgb
6. 在相同拆分和三个种子上训练 RGB ACT 与 RGB-D ACT
7. 对固定留出 episode 清单执行 evaluate_policy.py
8. 执行 compare_expert_runs.py / summarize_act_evaluations.py
9. 运行轻量 Diffusion 的匹配对照
10. 打包源码、锁定文件、日志、指标和复现命令
```

当前 Radeon 采集任务只是数据生成，不是最终模型能力结论。训练前必须先完成审计，按
profile 拆分 train、validation 和固定 held-out 集。

`scripts/build_dataset_split.py` 是复现边界：它把 audit 中的原始 episode ID 映射到 LeRobot
紧凑的成功回合索引，按包裹 profile 分层，并输出 ACT 与 Diffusion 共用的精确 episode 列表。
缺少 `summary.json`、metadata/计数不一致或多任务数据都会被主动拒绝。

watch_and_train_rocm.sh 可以等待采集 summary、生成清单并启动顺序 ACT 矩阵；未完成数据不会
触发训练，编排过程写入独立日志。

## 优化门禁

1. **数据门禁：**至少 300 个成功且按 profile 均衡的 RGB-D 回合；保存不可变清单和哈希。
2. **模型门禁：**RGB ACT、RGB-D ACT、轻量 Diffusion 使用相同拆分、三个种子和明确预算。
3. **任务门禁：**每个候选至少 30 个未参与选模的闭环回合，最终固定比较集至少 60 回合。
4. **安全门禁：**候选不得超过 35 N 接触力或增加掉落率；报告首次成功、恢复、掉落及分层结果。
5. **性能门禁：**在同一张 Radeon 上报告同步计时的平均/P95 延迟、samples/s、峰值显存和 GPU 利用率。
6. **扩展门禁：**VLA、吸盘、cradle、点云或 ROS 2 必须等前述门禁通过，并完成新增依赖/许可证审计。

## 证据规则

接口烟雾只能证明链路能运行，不能证明任务泛化。技术报告中的每项能力声明都应链接确切
命令、环境、episode 清单、summary JSON、失败轨迹和检查点哈希。被拒绝候选保留在
`evidence/` 作为负对照，不应悄悄改变基线。

学习和决策过程见：

- `ENGINEERING_DECISION_LOG_CN.md`
- `DEVELOPMENT_JOURNAL_CN.md`
- `OPTIMIZATION_ROADMAP_CN.md`
- `RESEARCH_AND_MODEL_MATRIX_CN.md`
- `DATASET_CARD_CN.md` 与 `MODEL_CARD_CN.md`
