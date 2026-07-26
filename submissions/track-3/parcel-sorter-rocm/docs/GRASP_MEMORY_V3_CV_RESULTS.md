# Conservative Grasp Memory V3: Train-Only CV Result

## Claim Boundary

This is a negative, train-only out-of-fold feasibility result. It does not use
the v2 development split or any holdout data, it is not an independent
generalization result, and it does not authorize new physical execution. The
frozen protocol is documented in `GRASP_MEMORY_V3_CV_PROTOCOL.md`.

## Execution and Integrity

The frozen 32-group v2 train dataset contains eight groups from each of four
parcel profiles and six candidates per group, for 192 recorded rollouts. Four
deterministic folds kept each physical group intact and placed two groups from
every profile in each fold. The protocol audit returned `protocol_valid` and
verified that development and holdout inputs were forbidden.

The cross-validation ran with PyTorch 2.9.1 and HIP 7.2 on one `gfx1100` AMD
Radeon. PyTorch reports the ROCm compatibility device as `cuda`; the physical
device recorded by the run is `AMD Radeon Graphics`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `grasp-memory-v3-train-only-cv.json` | 998,070 | `3ec39a321f88ac775340a40a57f74c2d6f17ffc51ee70450916d9ec15f168d68` |
| `grasp-memory-v3-cv-protocol-audit.json` | 2,553 | `c8058dfb7bdebbd2e210eeeb65e83837d8b4014d846447fff135951f88eeae8b` |

The protocol SHA-256 is
`80911bf25a2642fe0b099ab27d22fbd8e04ffdc40bc91434aa465405e4893b02`.
The source dataset SHA-256 is
`71761164467ba3b29866d87639b73474a5d5f2cc1fdb8907d62957a6c73703d5`.

## Result

The out-of-fold static baseline produced 7/32 successes and 17/32 safety
aborts. None of the six preregistered memory configurations passed.

| Candidate | Successes | Safety aborts | Changed choices | Warm P95 | Gate result |
| --- | ---: | ---: | ---: | ---: | --- |
| `knn-k3-r3-q90` | 7 | 17 | 0 | 0.534 ms | No task or safety improvement |
| `knn-k5-r3-q90` | 7 | 17 | 1 | 0.540 ms | No task or safety improvement |
| `knn-k5-r6-q90` | 7 | 17 | 2 | 0.552 ms | Fold safety regression; no net improvement |
| `knn-k5-r6-q95` | 7 | 17 | 2 | 0.542 ms | Fold safety regression; no net improvement |
| `knn-k9-r6-q95` | 7 | 17 | 0 | 0.555 ms | No task or safety improvement |
| `knn-k9-r15-q95` | 7 | 18 | 1 | 0.552 ms | Profile and fold safety regression; no net improvement |

All latency measurements are far below the frozen 5 ms limit. The failure is
therefore not a Radeon inference-latency bottleneck. Conservative abstention
mostly reproduced the static baseline, while the few changed selections did
not create a task or safety gain.

## Decision

The fixed selector returned:

```text
status=no_cv_candidate
selected=null
new_physics_authorized=false
```

No v3 learning population will be collected for this static-feature memory
ranker. No holdout was opened, and the static geometry baseline remains the
active runtime selector. The existing v2 development split must not be reused
to alter these thresholds or select another static 28-feature model.

The next admissible research direction must add information that the static
candidate descriptors do not contain, such as a separately preregistered,
short pre-grasp or micro-lift physics probe with contact/slip state. Batched
short-horizon rollout on Radeon is a plausible ROCm optimization target, but
it remains a proposal until its population, safety stop, comparison, and
holdout boundary are frozen in a new protocol.

The compact machine-readable decision is
`evidence/training/grasp-memory-v3-cv-evidence.json`.
