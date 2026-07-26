# 移动 SmolVLA 自动自我改进周期

## 目的

`scripts/run_mobile_self_improvement_cycle_rocm.py` 将移动双臂 SmolVLA 的失败回放、
专家课程采集、数据审计、Radeon 训练、离线 Harness 消融、冻结闭环评估和 checkpoint
晋级串成一条可恢复命令。它是回合之间运行的受控离线改进，不会在机器人正在执行动作时
修改权重。

## 当前 v3 周期

- 输入失败：冻结 v2 中 0.72 kg 中型纸箱在吸盘锁存前抬升失败；
- 自动桥接：保持尺寸、摩擦和偏移不变，将质量降到 0.648 kg；
- 训练课程：原六个成功专家实例加一个桥接实例，共七个；
- 新冻结集：训练开始前用种子 `20260728` 生成并哈希 100 个未见参数回合；
- 分层：小纸箱、扁平件、电子盒和中型纸箱各 25 个；
- 隔离：episode ID 和完整物理参数均不得与训练课程相同。

旧 v2 留出结果一旦用于生成桥接课程，就明确降级为开发证据，不能再作为 v3 的留出结果。

## Radeon 执行

```bash
cd /workspace/parcel-sorter-opt-v1
/workspace/rdna/bin/python scripts/run_mobile_self_improvement_cycle_rocm.py \
  --cycle-id v3 \
  --cycle-dir outputs/mobile-self-improvement-v3-cycle1 \
  --source-campaign-audit outputs/source-frozen-holdout-v2-audit.json \
  --base-training-config configs/mobile_suction_collection_v1.json \
  --baseline-checkpoint outputs/train/mobile-smolvla-mass-aware-b8w4-2400step-v2/checkpoints/002400/pretrained_model \
  --holdout-trials 100 --holdout-seed 20260728 \
  --training-steps 2800 --batch-size 8 --num-workers 4 --policy-hz 3 \
  --evaluation-workers 4
```

中断后增加 `--resume`。可用 `--dry-run` 只冻结配置并检查命令，也可用
`--stop-after <阶段>` 做受控分段。恢复时若失败清单、训练课程或冻结集发生变化，程序拒绝继续。

## 晋级门

候选 checkpoint 只有同时满足以下条件才会写入 `promoted-checkpoint.json`：

- 基线和候选均在同一套至少 100 回合的冻结集上完成；
- 候选成功率至少 80%；
- 相对基线的成功率点估计和 Wilson 95% 下界均不劣于 5 个百分点；
- 接触力越界为零；
- 每个回合都有 VLA 实际执行；
- 每个回合均记录为单张 AMD Radeon 和 ROCm。

未通过只写出 `completed_not_promoted` 和逐项失败原因，不覆盖现有 checkpoint。

## 2026-07-27 实测结果

周期已在单张 AMD Radeon `gfx1100` 和 ROCm 7.2.1 上完整执行。七个课程回合全部成功，
其中自动生成的 0.648 kg 桥接件放置误差为 1.30 cm、峰值接触力为 8.60 N。合并数据集
包含 4,557 帧，状态/动作维度为 43/19，六个任务阶段完整且策略输入无特权位姿。

SmolVLA v3 使用 AMP、batch 8 和四个 worker 训练 2,800 步（4.92 epoch），耗时约
7 分 20 秒，峰值显存 2.21 GB，末步 loss 0.037。42 个训练内阶段样本的离线结果为：

| 方法 | 平均 MAE | 安全包络通过 |
| --- | ---: | ---: |
| 原始 v3 VLA | 0.019790 | 0/42 |
| 直接安全限幅 | 0.020893 | 42/42 |
| Harness-Lite | 0.005370 | 42/42 |
| 同执行器专家 | 0.004468 | 42/42 |

四路隔离评测将 GPU 利用率从顺序模式约 13% 提高到最高约 85%，每个回合仍记录同一张
Radeon。收集器审计发现两个缺失 summary 的基础设施失败，并在修复负科学计数法 CLI
参数后按相同配置补跑；它们不被误计为任务失败。

| 冻结 100 回合 | v2 基线 | v3 候选 |
| --- | ---: | ---: |
| 总成功率 | 96/100 | 91/100 |
| Wilson 95% | 90.16%--98.43% | 83.77%--95.19% |
| 小纸箱 | 25/25 | 23/25 |
| 扁平件 | 22/25 | 22/25 |
| 电子盒 | 25/25 | 25/25 |
| 中型纸箱 | 24/25 | 21/25 |
| 成功回合平均放置误差 | 1.40 cm | 1.06 cm |
| 35 N 力越界 | 0 | 0 |

配对结果为双方成功 90、双方失败 3、v3 修复 1、v3 新增失败 6。v3 达到绝对 80%、
点估计不劣性、零力越界、全量 VLA 执行和单卡 ROCm 门，但 Wilson 下界不劣性失败，
因此自动状态为 `completed_not_promoted`，v2 继续作为正式 checkpoint。该消融表明单个
边界桥接样本能降低成功放置误差和离线动作误差，但不足以保证整个参数分布的闭环成功率。

## 可审计产物

周期目录保存源文件 SHA-256、冻结集哈希、每一步的精确命令、独立日志、数据审计、
离线消融、基线/候选紧凑闭环证据、Wilson 区间和晋级决策。完整数据及模型仍保存在
Radeon 工作区；Git 仅提交小体积协议、代码和紧凑证据。
本次紧凑证据及 SHA-256 位于 `evidence/mobile_bimanual/self_improvement_v3/`。
