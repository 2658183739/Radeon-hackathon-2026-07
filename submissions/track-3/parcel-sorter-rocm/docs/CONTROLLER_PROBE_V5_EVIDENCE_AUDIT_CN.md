# 控制器探针 V5 终态证据审计

## 状态与目的

审计器已经实现并通过测试，但只有 V5 写出最终 manifest、dataset 和 result 后才能运行。它只做
不观察结果的完整性校验，不是第二套策略选择器或统计 evaluator。

它检查精确的 80 个预注册 `(profile, episode)` 键、每 profile 十组、非 dry-run 的 ROCm 来源、
manifest 与 dataset 的源路径/哈希一致性、协议/manifest/dataset 文件绑定、dataset 载荷哈希及终态
授权不变量。重复或替换 episode、CPU 或 dry-run 证据、陈旧源文件、profile 数量错误和授权漂移都
会被拒绝。

审计器不读取候选结果行，不重新选择候选，不重算指标，也不能改变失败结论。即使通过，也只授权
预注册的在线 Radeon pilot；运行时激活与 V2 holdout 仍然禁止。

## 执行命令

两个最终 JSON 均存在后，从 `/workspace/parcel-sorter-opt-v1` 执行：

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/audit_controller_probe_confirmation_evidence.py \
  --protocol configs/controller_probe_confirmation_v5.toml \
  --manifest outputs/controller-probe-v5/candidates/confirmation/manifest.json \
  --dataset outputs/controller-probe-v5/confirmation-dataset.json \
  --result outputs/controller-probe-v5/confirmation-result.json \
  --output outputs/controller-probe-v5/confirmation-evidence-audit.json
```

必须同时满足退出码 `0`、`status=evidence_valid` 和空 `errors`。七项定向测试与完整本地测试均通过：
343 项成功，1 项因本地缺少 PyTorch 按环境跳过。设计和测试审计器期间没有读取 V5 结果。
