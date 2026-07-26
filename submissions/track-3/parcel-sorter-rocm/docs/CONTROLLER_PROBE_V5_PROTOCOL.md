# Controller Probe V5: Independent Confirmation Protocol

## Current Status

V5 is preregistered and ready for the first Radeon physics run. No V5 task
outcome has been observed yet. The protocol audit is valid, the collection
dry run contains 80 groups and at most 480 candidate rollouts, and the full
local suite passes 304 tests with one environment-dependent skip.

This stage evaluates only the frozen `veto-static` mechanism selected by V4.
It does not reopen the rejected MLP, KNN, or active probe rankings, and it does
not read V2 development or holdout data.

## Why This Population Is Independent

All 80 `(profile, episode)` keys use new 9.1M--9.8M namespaces and have zero
overlap with every V2 train, development, and holdout assignment. Episode
selection reads deterministic parcel samples and a box/end-effector
compatibility predicate only. It does not construct a Genesis scene, solve
IK, execute the controller, or inspect force, success, or drop outcomes.

The population contains ten groups for each of eight rigid, parallel-jaw box
profiles:

| Population role | Profiles |
| --- | --- |
| Previously represented profile, new episodes | `medium_carton`, `shoe_box_proxy`, `large_narrow_carton`, `near_limit_box` |
| Profile unseen by V4 selection | `small_carton`, `flat_mailer`, `long_carton`, `electronics_box` |

This deliberately broadens dimensions, mass, friction, yaw, and camera noise
without pretending that the current box grasp planner supports cylinders.
Upright canisters and mailing tubes remain separate capability targets because
the registered candidate generator is box-specific. Mixing them into this
confirmation would test a new planner and the safety veto at the same time.

## Frozen Intervention

The collection enumerates up to six collision-checked static grasp candidates
for every rigid box, including boxes below the old tall-box activation
threshold. Every candidate runs in a fresh Genesis scene through the unchanged
controller and 35 N supervisor on one AMD Radeon through ROCm.

For ranking, each candidate trace is causally truncated at the first
post-lift/pre-place observation. A candidate is eligible only after completing
the micro-lift below 35 N, acquiring and retaining contact, and lifting the
parcel. `veto-static` then preserves static order among eligible candidates.
If none is eligible, it records a task failure and safe abstention; it cannot
silently execute the baseline candidate.

The all-box candidate-enumeration scope is isolated in the V5 collection path.
The shared V2/V3 activation constant is unchanged, so their frozen hashes and
audits remain valid.

## Confirmation Gate

The result passes only when all conditions hold:

- all 80 groups and ten groups per profile are present;
- there is no paired success loss, safety-abort regression, or drop regression;
- every profile has zero success loss and zero safety-abort regression;
- at least six paired safety-abort reductions are observed;
- reductions occur in at least two profiles;
- the one-sided exact paired test for fewer safety aborts is at most 0.05;
- six-candidate host selection P95 is below 5 ms.

Success, force abort, and drop use paired exact McNemar counts and Wilson 95%
rate intervals. Executed-pair peak force and duration use deterministic paired
bootstrap intervals and sign-flip tests. Results are also split by profile
novelty, yaw, friction, camera-noise norm, and mass. Probe frames are reported
separately from full-rollout duration.

A pass authorizes only an online Radeon-parallel clone-and-probe pilot. It
does not activate `veto-static` in the submitted runtime. A failure closes the
mechanism without threshold tuning on these outcomes.

## Radeon Execution

From `/workspace/parcel-sorter-opt-v1`, audit before starting physics:

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/audit_controller_probe_confirmation_protocol.py \
  --protocol configs/controller_probe_confirmation_v5.toml \
  --output outputs/controller-probe-v5/protocol-audit.json
```

Collect the independent population. `--resume` validates and preserves every
completed source before continuing after an interruption:

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

After all 80 sources are complete, evaluate exactly once:

```bash
PYTHONPATH=src /workspace/rdna/bin/python \
  scripts/evaluate_controller_probe_confirmation.py \
  --protocol configs/controller_probe_confirmation_v5.toml \
  --manifest /workspace/parcel-sorter-opt-v1/outputs/controller-probe-v5/candidates/confirmation/manifest.json \
  --dataset-output outputs/controller-probe-v5/confirmation-dataset.json \
  --output outputs/controller-probe-v5/confirmation-result.json
```

The frozen protocol SHA-256 is
`062e3ec9d0c4968b1593331ada5aa1aa737e4eadda869e173fe0116e3ab8101e`.
