# Controller Probe V5 Terminal Evidence Audit

## Status and purpose

The auditor is implemented and tested but must run only after V5 writes its
final manifest, dataset, and result. It is an outcome-blind integrity check,
not a second policy selector or statistical evaluator.

It verifies the exact preregistered 80 `(profile, episode)` keys, ten groups
per profile, non-dry-run ROCm provenance, manifest-to-dataset source path/hash
identity, protocol/manifest/dataset file bindings, the dataset payload hash,
and terminal authorization invariants. It rejects duplicate or substituted
episodes, CPU or dry-run evidence, stale sources, malformed profile counts,
and authorization drift.

The audit does not inspect candidate outcome rows, reselect candidates,
recompute metrics, or change a failed result. A valid passing result authorizes
only the preregistered online Radeon pilot; runtime activation and V2 holdout
remain forbidden.

## Command

Run from `/workspace/parcel-sorter-opt-v1` after both final JSON files exist:

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/audit_controller_probe_confirmation_evidence.py \
  --protocol configs/controller_probe_confirmation_v5.toml \
  --manifest outputs/controller-probe-v5/candidates/confirmation/manifest.json \
  --dataset outputs/controller-probe-v5/confirmation-dataset.json \
  --result outputs/controller-probe-v5/confirmation-result.json \
  --output outputs/controller-probe-v5/confirmation-evidence-audit.json
```

Require exit code `0`, `status=evidence_valid`, and an empty `errors` list.
Seven directed tests and the complete local suite of 343 tests pass, with one
environment-dependent PyTorch test skipped. No V5 outcome was read while
designing or testing this auditor.
