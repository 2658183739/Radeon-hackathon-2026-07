# 多模态优化工程记录：2026-07-25

本文是可学习、可审计的工程记录，不是私有逐字思维链。每一步都记录可观察输入、候选、
决策、原因、代码位置和验证结果。

## 本轮结果

- 修复 1,000 倍深度尺度错误：Genesis 光栅相机深度本来就是米，不能再乘 `0.001`。
- 同时保存原始米制深度和适配 LeRobot 三通道视觉骨干的确定性深度视图。
- 新增数据质量门禁：旧数据可以继续训练 RGB 基线，但明确禁止用于 RGB-D。
- 学习策略根据检查点配置自动发现是否需要第二视觉输入。
- 在单张 Radeon 上完成新数据采集、一次 ACT RGB-D 更新、保存、重载和 Genesis 闭环推理。
- 单步模型没有被写成任务能力提升。

## 逐步记录

| 步骤 | 证据或事件 | 决策与原因 | 验证 |
| --- | --- | --- | --- |
| 1 | 旧 metadata 写米，但深度中位数只有 `0.00117156` | 先判定传感器问题，不急着加模型 | 与真实相机距离比较 |
| 2 | 源码统一把 Genesis 深度乘 `0.001` | 查上游实现，不靠修改 metadata 掩盖 | 相机 near/far 明确为米；点云直接使用深度 |
| 3 | 上游单位和场景尺度都说明原值是米 | 删除换算并保留 float32 | 单测保持 `0.8` 与 `3.4185` m |
| 4 | ACT/Diffusion 的 ResNet 输入需要三通道 | 原始深度保留，再生成 0.25-4.0 m 反向归一化灰度三通道视图 | 形状、dtype、裁剪和无效像素单测 |
| 5 | 旧数据缺派生视图且尺度错误 | 训练前做 metadata 审计；RGB 警告，RGB-D 硬拒绝 | 旧 RGB 审计通过但告警；RGB-D 退出码 2 |
| 6 | 手工推理开关可能和检查点不一致 | 从检查点配置读取视觉特征 | 旧 RGB 检查点兼容；未知相机键拒绝 |
| 7 | Radeon 新采一个回合 | 训练前先验传感器单位 | 152 帧；范围 `0.737-3.535` m，中位数 `1.164` m；审计通过 |
| 8 | 第一次单步训练用 split 0 但仍要求 eval | 归类为配置错误，不归因于 ROCm/RGB-D | LeRobot 在建模前拒绝 |
| 9 | 该非法组合以后还可能发生 | shell 预检：split 为 0 时 eval steps 必须为 0 | Bash 语法通过，修正后启动 |
| 10 | RGB-D ACT 同时读取两路视觉 | 只作为链路证据 | 51,577,736 参数；一次更新；进度 2.71 秒；峰值 0.98 GB |
| 11 | 保存的检查点声明两路相机 | 通过通用安全适配器进入闭环 | 无接口错误；平均 3.48 ms，P95 11.53 ms |
| 12 | 单步模型任务失败 | 保留失败，不使用能力宣传语 | 0/1，未触发接触力；仅证明接口 |

第一次远程验证包装命令在 71 项测试和两次审计已经完成后，被 PowerShell/Bash 变量展开
影响了最后的预期退出码断言。改用单引号远程输入后，RGB-D 拒绝准确返回 2。该事件属于
编排命令失败，不是项目代码失败。

## 代码能力对应

| 文件 | 新能力 | 边界 |
| --- | --- | --- |
| `genesis_env.py` | 正确 float32 米制深度 | 不伪造修复旧数据 |
| `dataset.py` | 原始深度与确定性深度视图 | 固定 0.25-4.0 m 只是消融输入，不是真机标定 |
| `data_quality.py` | 特征形状与深度合理性审计 | 读取 metadata，不逐像素扫描 |
| `audit_dataset.py` | CLI 门禁和 JSON 证据 | RGB-D 特征/尺度不合法则失败 |
| `policy.py` | 根据检查点组装 RGB 或 RGB-D batch | 只支持已声明的顶视 RGB/深度视图 |
| `train_act_rocm.sh` | `ACT_USE_DEPTH=true` 与 split/eval 门禁 | 需要新采集数据 |
| `train_diffusion_rocm.sh` | `DIFFUSION_USE_DEPTH=true` 与配置门禁 | 效果仍待正式训练 |

## 使用方法

旧数据按 RGB 模式审计：

```bash
python scripts/audit_dataset.py --dataset-root <dataset>
```

要求有效 RGB-D 并训练：

```bash
python scripts/audit_dataset.py --dataset-root <dataset> --require-depth-rgb
ACT_USE_DEPTH=true ACT_STEPS=30000 ACT_SEED=42 \
  bash scripts/train_act_rocm.sh <dataset> outputs/train/act-rgbd-seed42
```

匹配 RGB 对照只把 `ACT_USE_DEPTH=false`，其余数据、种子和训练预算保持一致。不同条件绝不
复用输出目录。

## 下一验收门

采集 15 个完整 catalog-v2 配比块；如果所有目标类别都能完成，应得到 300 个成功回合。
困难类别失败时不能偷偷换成简单类别。冻结 episode 清单后，RGB 与 RGB-D ACT 各训练
3 个种子。只有留出闭环成功率提升、掉落和接触力不退化，并报告延迟代价，才保留深度。
