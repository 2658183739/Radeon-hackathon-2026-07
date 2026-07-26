# 控制器保真探针 V5：独立确认协议

## 当前状态

V5 已完成预注册，可以开始第一次 Radeon 物理运行，但尚未观察任何 V5
任务结果。协议审计已通过；采集 dry-run 固定为 80 组、最多 480 条候选
rollout；本地完整测试为 304 项通过、1 项按环境跳过。

本阶段只确认 V4 已选定的 `veto-static` 机制。已被拒绝的 MLP、KNN 和三个
主动重排策略不会重新进入比较；V2 development 与 holdout 继续禁止读取。

## 为什么这是独立总体

80 个 `(profile, episode)` 键全部位于新的 910 万至 980 万命名空间，与 V2
train、development、holdout 的所有键零重叠。样本选择只读取确定性随机化
后的包裹参数，以及“刚性箱体 + 平行夹爪”兼容条件；它不构造 Genesis
场景、不求解 IK、不执行机器人，也不读取力、成功、掉落等结果。

8 个 profile 各 10 组：

| 总体角色 | Profile |
| --- | --- |
| V4 出现过的类别，但使用全新 episode | `medium_carton`、`shoe_box_proxy`、`large_narrow_carton`、`near_limit_box` |
| V4 选择阶段未见类别 | `small_carton`、`flat_mailer`、`long_carton`、`electronics_box` |

该设计扩展了尺寸、质量、摩擦、yaw 和相机噪声覆盖，但不虚构当前抓取规划器
已经支持圆柱体。立式罐体和快递筒需要另一套圆柱抓取候选规划；若在本次确认
中混入圆柱，会同时改变规划器和安全否决器，无法归因。

## 冻结的干预方式

V5 对每个刚性箱体枚举最多 6 个经过碰撞检查的静态抓取候选，包括低于旧版
“高箱体”激活阈值的包裹。每个候选都在全新 Genesis 场景中，使用原控制器和
35 N 安全监督器，在单张 AMD Radeon GPU 与 ROCm 上完整执行。

排序输入只保留首次抬升完成、开始 `place` 动作前的因果轨迹前缀。候选必须在
35 N 以下完成微抬升、取得并保持接触、确认包裹已离台，才算合格。
`veto-static` 只在合格候选中保持原静态顺序；若没有合格候选，则明确记录任务
失败和安全放弃，不能暗中回退执行静态首选。

“全部刚性箱体”枚举只存在于 V5 独立采集入口。V2/V3 共用的激活常量没有改变，
所以旧协议的冻结哈希和审计仍然有效。

## 确认门槛

只有同时满足以下条件才通过：

- 80 组全部完成，且每个 profile 恰好 10 组；
- 配对比较中不存在成功损失、安全中止新增或掉落新增；
- 每个 profile 都不存在成功损失或安全回归；
- 至少减少 6 次安全中止；
- 安全收益至少分布在 2 个 profile；
- “候选方案安全中止更少”的单侧精确配对检验不大于 0.05；
- 6 候选选择器 P95 小于 5 ms。

成功、力中止、掉落分别报告 McNemar 精确配对计数和 Wilson 95% 区间；只对
实际执行的配对报告峰值力、耗时、确定性配对 bootstrap 区间与符号翻转检验。
此外按新旧 profile、yaw、摩擦、相机噪声范数和质量分层。探针帧成本与完整
rollout 耗时分开记录。

通过只授权下一步“Radeon 并行场景克隆 + 在线短探针”试验，不会直接启用运行
时策略。若失败，则关闭该机制，不能根据本次结果再调阈值。

## Radeon 执行顺序

在 `/workspace/parcel-sorter-opt-v1` 中先审计：

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/audit_controller_probe_confirmation_protocol.py \
  --protocol configs/controller_probe_confirmation_v5.toml \
  --output outputs/controller-probe-v5/protocol-audit.json
```

开始采集；实例中断后可用同一命令继续，`--resume` 会先校验已有文件：

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/run_controller_probe_confirmation_collection.py \
  --protocol configs/controller_probe_confirmation_v5.toml \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --max-candidates 6 \
  --repeats 1 \
  --resume \
  --output-dir /workspace/parcel-sorter-opt-v1/outputs/controller-probe-v5/candidates
```

80 组全部完成后，只运行一次确认评估：

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/evaluate_controller_probe_confirmation.py \
  --protocol configs/controller_probe_confirmation_v5.toml \
  --manifest /workspace/parcel-sorter-opt-v1/outputs/controller-probe-v5/candidates/confirmation/manifest.json \
  --dataset-output outputs/controller-probe-v5/confirmation-dataset.json \
  --output outputs/controller-probe-v5/confirmation-result.json
```

冻结协议 SHA-256：
`062e3ec9d0c4968b1593331ada5aa1aa737e4eadda869e173fe0116e3ab8101e`。
