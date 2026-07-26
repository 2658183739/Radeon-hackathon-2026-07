# Controller-Faithful Probe V4: Train-Only Feasibility Protocol

## Purpose and Boundary

The v2 MLPs and v3 conservative memory ranker showed the same limitation in
different forms: 28 static geometry/state features did not predict later
contact dynamics reliably. V4 tests whether information already present in a
controller-faithful micro-lift can rank candidates better than the static
geometry baseline.

This is a train-only feasibility study. It may read the 32 frozen v2 train
groups and their 192 full candidate trajectories, but features must stop
before the first transport/place action. V2 development and holdout are
forbidden. Even a passing V4 policy reports `new_physics_authorized=false`;
online probes and a new physical population require another frozen protocol.

## Causal Cutoff

Each source trace records the current state before its command is executed.
The extractor includes the first row whose stage is `place`, because this is
the terminal observation produced by the preceding lift command, then rejects
every later row. An early `abort` is also a valid boundary. This gives the
probe access to approach, grasp, verify, lift, and the post-lift boundary
state, but not transport, release, task success, or later force events.

Tests enforce two leakage boundaries:

1. Mutating force, relative pose, contact, or slip after the boundary cannot
   change any probe feature.
2. Swapping final labels between candidates cannot change which candidate a
   policy selects.

## Frozen Feature Contract

The 27 features are physical summaries, not learned embeddings:

- completion, early force-abort, contact acquisition, terminal contact, and
  terminal lifted flags;
- probe/verify/lift frame counts and contact acquisition latency;
- approach, verify, lift, terminal, and total force statistics;
- parcel and end-effector lift displacement;
- terminal relative-pose drift, maximum relative step, and maximum downward
  relative step;
- loaded-phase contact retention fraction.

No final success, final safety-abort label, full-horizon peak force, duration,
terminal stage, or post-boundary row is present in the ranking key.

## Eligibility and Policies

A candidate is eligible only if the micro-lift completed, its probe stayed at
or below the unchanged 35 N line, contact was acquired and retained, and the
parcel was lifted at the boundary. If none is eligible, the planner returns a
safe abstention. It does not execute the static candidate as a hidden fallback.

Four fixed, parameter-free orderings are compared:

| Policy | Ordering after hard eligibility |
| --- | --- |
| `veto-static` | Preserve static geometry order |
| `force-first` | Probe peak force, downward motion, drift, static order |
| `stability-first` | Downward step, total relative step, drift, force, contact support, static order |
| `support-first` | Contact retention, parcel lift, drift, force, static order |

These alternatives distinguish veto-only use from three physically motivated
ranking priorities without fitting thresholds to observed outcomes.

## Fixed Evaluation and Gate

All 32 train groups are assigned to four deterministic, profile-balanced
folds, with two groups from every profile in every fold. Policies do not train
on a fold; the folds expose local regressions and prevent an aggregate gain
from hiding a concentrated failure.

A policy requires complete groups, no safety or success regression in any
profile, no safety or success regression in any fold, no aggregate success
regression, at least one aggregate success gain or safety-abort reduction, and
six-candidate selector P95 below 5 ms. Safe abstention is counted as task
failure and therefore cannot manufacture a passing result by suppressing all
execution.

Eligible policies are ordered by fewer safety aborts, more successes, fewer
abstentions, lower selected-candidate force, latency, and fixed name. A passing
policy still does not authorize development or holdout.

## Reproduction Order

After the protocol commit exists, run the audit first:

```bash
cd /workspace/parcel-sorter-opt-v1
PYTHONPATH=src /opt/venv/bin/python \
  scripts/audit_controller_faithful_probe_protocol.py \
  --protocol configs/controller_faithful_probe_v4.toml \
  --output outputs/controller-probe-v4/protocol-audit.json
```

Only after `protocol_valid` may the train-only evaluator run:

```bash
PYTHONPATH=src /opt/venv/bin/python \
  scripts/evaluate_controller_faithful_probe.py \
  --manifest /workspace/parcel-sorter-opt-v1/outputs/grasp-scorer-v2/candidates/train/manifest.json \
  --protocol configs/controller_faithful_probe_v4.toml \
  --dataset-output outputs/controller-probe-v4/train-probe-dataset.json \
  --output outputs/controller-probe-v4/train-only-result.json
```

The protocol SHA-256 is
`ca941366101c0a0d730a2628c442573347113e539c541778b617ba0619be4ff3`.
