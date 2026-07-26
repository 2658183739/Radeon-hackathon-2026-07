# 圆柱候选总体 V1 审计结果

## 结论

提交 `4788d21` 先冻结 128 个样本、规划参数、解析误差门和四份实现哈希；随后才运行正式审计。
结果为 `candidate_population_valid`，128/128 样本通过且 `errors=[]`。

这证明 catalog 中当前平行夹爪可处理的两类圆柱都能产生有限、唯一、与筒轴一致的解析候选。
它不包含 IK、碰撞、物理步进或任务结果，因此只授权下一阶段静态 ROCm IK/碰撞筛查，不授权
闭环成功、运行时激活或论文正向结论。

## 总体与结果

| Profile | 样本 | 观察尺寸范围 | 每样本候选 | 最小开口余量 | 最大轴误差 |
| --- | ---: | --- | ---: | ---: | ---: |
| `upright_canister` | 64 | 直径 40.66–69.71 mm，高度 60.43–158.12 mm | 16 | 10.29 mm | 0 |
| `mailing_tube` | 64 | 长度 160.38–299.60 mm，直径 35.24–64.94 mm | 18 | 15.06 mm | `4.44e-16` |

卧式候选的接近方向与筒轴最大点积绝对值为 `2.74e-16`，四元数范数最大误差为 0。
所有 64 个卧式样本的滚动风险指数上界为 0.2；该值是固定排序启发式，不是失败概率。

## 因果边界

审计器记录：

```json
{
  "outcome_fields_read": [],
  "scene_constructed": false,
  "robot_action_executed": false,
  "physics_stepped": false
}
```

样本来自两个独立 episode 命名空间：立式从 `10100000` 开始，卧式从 `10200000` 开始，各 64 个。
它们只依赖冻结 catalog 和确定性 `DomainRandomizer`，没有根据成功、受力或可达性选样。

## 哈希

```text
protocol SHA-256:
57404ae62ce0b9094bf600a84eeb007e0ae480452b6d1eab4a7452c4f3ac410a

population SHA-256:
1aeaf2993f64d0a3b6dd970e93f0fa1f622e3b043984e80020f8f2df9b5cfcf5

result-file SHA-256:
1c19e5a0f5d35b1d2f8a234053057af40f5049ab96e23607b64f20fea16adf2c
```

完整 136,094 字节结果保存在
`evidence/planning/cylinder-candidate-audit-v1.json`。

## 复现

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/audit_cylinder_candidate_population.py \
  --protocol configs/cylinder_candidate_audit_v1.toml \
  --output outputs/cylinder-candidate-audit-v1/result.json
```

下一步必须从这 128 个样本中按冻结规则建立静态 IK/碰撞屏幕，报告“候选存在”和“机器人可达”
之间的差距。若某个 profile 的可行率不足，先修改候选几何并使用新的开发总体，不能把本结果改写成
物理支持证据。
