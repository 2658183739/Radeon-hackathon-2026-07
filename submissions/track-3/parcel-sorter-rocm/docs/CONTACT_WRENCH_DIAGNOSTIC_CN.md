# 接触扳手稳定性诊断

## 范围与决策

本实验检查：实测夹指接触几何和受力，能否在长距离搬运前拒绝不稳定抓取。实验只使用已经观察过的
机理回合 `4120001` 和冻结训练组 `7130001`，没有打开任何 holdout 编号。固定早期窗口不能可靠
区分成功、任务失败和安全中止，因此该诊断不接入抓取排序。

本轮保留的成果是一层可审计遥测。下一项干预必须改变真实支撑几何，例如引入带版本和许可证的
快递夹具适配器，而不是继续根据这些结果拟合阈值。

## 已核实的 Genesis 接口

在单张 Radeon `gfx1100` 上探测 Genesis 1.2.3 后，`get_contacts()` 实际返回 `geom_a`、
`geom_b`、`link_a`、`link_b`、`position`、`normal`、`penetration`、`force_a` 和
`force_b`，所有张量都位于 PyTorch 的 `cuda:0`，这是 ROCm 设备在 PyTorch 中的名称。代码不依赖
geom A/B 顺序，统一把力转换为“作用在包裹上的力”。

只读指标包括：

- 双指接触与左右受力不对称；
- 接触点相对包裹质心的力臂；
- 法向/切向力与库仑摩擦锥余量；
- 加入重力后的合力、合力矩残差；
- 对 1.5 m/s2 有界运输扰动的剩余承载能力；
- 未改变的 35 N 实测接触力边界。

归一化质量分是上述物理分量的几何平均，只是诊断分数，不是学习得到的成功概率。遥测默认关闭，
既不改变控制动作，也不改变候选排序。

## 固定预测窗口

最终路径只在每个 30 Hz 控制帧的最后一个物理子步采样。报告两个固定 0.1 秒窗口，每个 3 个样本：

1. 包裹第一次抬升到 5 mm 之前的最后三个双指接触样本；
2. 抬升达到 5 mm 后最早的三个带载样本。

窗口选择不查看后续任务结果。完整搬运事件仍可写入诊断文件，但不用于“提前预测”的结论。

## 开发结果

在 `4120001` 中，成功的中心 `+45 mm` 候选比失败的 `+40 mm` 候选具有更大的早期摩擦和扰动
余量。这个方向有价值，但不足以接入：两个早期带载窗口都被判为 robust，质量均值分别为 0.869
和 0.858。

冻结的 `7130001` 组否定了简单门槛。三次成功和三次失败的指标明显重叠：一个成功候选的抬升前
robust 比例为 0，而一个后来达到 100.70 N 的安全中止候选，抬升前 robust 比例为 1。成功候选的
早期带载质量均值范围为 0.710--0.900，失败候选为 0.515--0.895。因此 robust 布尔值和综合
质量分都没有达到接入所需的预测有效性。

## ROCm 调度结果

向量化 PyTorch 版本与纯 Python 参考实现逐项一致到小数点后五位，但每次约 8 个接触点时反而更慢。
在 240 Hz 遥测下，两条 rollout 的总时间从参考路径 93.98 秒增加到 ROCm 小算子路径 101.65 秒；
两条 rollout 的指标平均延迟分别从 `6.84/4.06 ms` 增加到 `7.81/5.29 ms`。这是可复现的负优化
结果，不能宣传为 GPU 加速收益。

最终默认使用 30 Hz 的 CPU 参考评分器，Genesis 物理和接触求解仍全部在 Radeon 上。降采样保持了
指标方向，把原始文件从 14.3 MB 降到 6.0 MB，并把匹配运行缩短到 86.66 秒。若将来要把该指标
接入在线流程，应先跨环境或跨控制帧形成批量，再交给 ROCm，不能逐个微小接触调用 GPU。

## 复现

```bash
python scripts/diagnose_counterfactual_grasp_candidates.py \
  --config configs/catalog_v2.toml \
  --profile medium_carton \
  --episode 4120001 \
  --backend rocm \
  --candidate-id canonical-long-+0.000-up-0.040 \
  --candidate-id canonical-long-+0.000-up-0.045 \
  --contact-wrench-telemetry \
  --contact-wrench-backend cpu \
  --output outputs/contact-wrench-development-v1/4120001.json
```

`--contact-wrench-backend rocm` 只用于复现小张量后端对照。紧凑证据和原始文件哈希位于
`evidence/expert/radeon-contact-wrench-development-v1.json`。
