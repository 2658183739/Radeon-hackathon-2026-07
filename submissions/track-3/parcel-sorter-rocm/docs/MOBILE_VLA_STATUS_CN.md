# 移动双臂 VLA 状态（2026-07-27）

## 已验证流程

移动平台是三自由度全向底盘加两条 Franka Panda 机械臂，共 21 DoF。左臂安装三个物理碰撞吸盘，
右臂安装 V 型托架。v41 成功专家回合使用左侧吸盘臂，尚未声称双臂协同承载成功。

在单张 AMD Radeon `gfx1100` 上，v41 对 0.4 kg 刚性包裹形成两个杯口密封，抬升 0.0811 m，
底盘携物运输 0.30 m，以 0.0118 m 最终误差完成放置和释放。全程零断吸，柔顺吸附力峰值
11.84 N，杯面接触峰值 2.37 N，均低于 35 N 任务中止线。

## 已审计数据集

v43 LeRobotDataset 包含一个完整成功回合：655 帧、30 Hz、224x224 RGB-D、43 维非特权状态和
19 维动作。六阶段均存在：预抓取 30 帧、接近 191 帧、抬升 90 帧、运输 224 帧、放置 90 帧、
释放 30 帧。7 维包裹真值位姿单独保存，不进入策略。原始 TIFF 深度为 2.61--20.00 m。有限值、
帧率、底盘速度、四元数、工具命令、深度单位和特权信息隔离审计全部通过。

## SmolVLA 训练

移动策略使用 LeRobot SmolVLA，并从 Apache-2.0 的
`HuggingFaceTB/SmolVLM2-500M-Video-Instruct` 初始化。配置共有 450,061,536 个参数，其中
99,896,352 个可训练；输入为 RGB、43 维状态和任务文本，输出为 19 维底盘/双臂动作。深度已采集，
但尚未输入本检查点。

50 步 Radeon pilot 已用 AMP 完成，报告峰值显存 1.79 GB。第 1--5 步平均 loss 为 2.4616，
第 46--50 步为 1.2410，最低 1.088。这只证明单回合训练链，不代表收敛或泛化。

## 六阶段检查点评估

评估器从每个阶段选择中位帧，每阶段重置动作队列，并固定使用随机种子
`20260727`--`20260732`。六次推理均产生有限的 19 维动作；热推理平均延迟 149.47 ms，P95 为
153.00 ms，与专家动作的阶段平均 MAE 为 0.1201。

六个原始动作中没有一个满足专家执行包络。模型输出的末端目标距离当前末端 0.054--0.469 m，
超过 0.04 m 单步上限；左吸盘命令方向也只在六阶段中的两个阶段与专家一致。安全执行器通过底盘限速、
笛卡尔限步、四元数归一化和工具二值化使六个动作均可数值执行。结论是 ROCm 检查点接口已通过，
但这个 pilot 不能直接接管闭环。

## 决策与下一门禁

不把 50 步检查点作为移动主控制器，将其冻结为欠训练基线。下一步采集包裹尺寸、质量、摩擦、位置、
相机扰动均变化的成功和失败回合，并平衡六阶段样本，再训练多回合检查点。只有离线动作包络明显改善后，
Harness-Lite 才能评估有界残差候选。晋级必须通过互不重叠的闭环测试集，并报告成功率、接触力、掉落、
延迟和分包裹指标；当前单回合结果不能称为移动泛化。

## 复现

```bash
python scripts/audit_mobile_dataset.py \
  --dataset-root outputs/mobile-suction-dataset-v43/lerobot_dataset \
  --output outputs/mobile-suction-dataset-v43/audit.json

MOBILE_SMOLVLA_STEPS=50 bash scripts/train_mobile_smolvla_rocm.sh \
  outputs/mobile-suction-dataset-v43/lerobot_dataset \
  outputs/train/mobile-smolvla-full-episode-50step-v1

python scripts/smoke_mobile_smolvla_inference_rocm.py \
  --checkpoint outputs/train/mobile-smolvla-full-episode-50step-v1/checkpoints/000050/pretrained_model \
  --dataset-root outputs/mobile-suction-dataset-v43/lerobot_dataset \
  --output outputs/eval/mobile-smolvla-50step-six-stage-v1.json \
  --seed 20260727
```
