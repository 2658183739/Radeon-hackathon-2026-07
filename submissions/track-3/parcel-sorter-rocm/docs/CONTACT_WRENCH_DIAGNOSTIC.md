# Contact-Wrench Stability Diagnostic

## Scope and decision

This experiment asked whether measured finger contact geometry and force could
reject unstable parcel grasps before long transport. It used only the already
observed mechanism episode `4120001` and frozen train group `7130001`. No
holdout ID was opened. The diagnostic remains disconnected from grasp ranking
because the fixed early windows did not separate success, task failure, and
safety abort reliably.

The useful outcome is an auditable telemetry layer. The next intervention must
change support geometry, such as a versioned parcel-gripper adapter, rather
than fit another threshold to these outcomes.

## Verified Genesis interface

Genesis 1.2.3 was probed on the single Radeon `gfx1100`. `get_contacts()`
returned `geom_a`, `geom_b`, `link_a`, `link_b`, `position`, `normal`,
`penetration`, `force_a`, and `force_b`; all tensors were on PyTorch device
`cuda:0`, which is the ROCm device name. Forces are standardized as acting on
the parcel regardless of geom-A/geom-B order.

The read-only metric uses:

- bilateral finger contact and force asymmetry;
- contact moment arms about the parcel center of mass;
- measured normal/tangential force and Coulomb friction-cone margin;
- residual force and torque after gravity;
- reserve against a bounded 1.5 m/s2 transport disturbance;
- the unchanged 35 N measured contact-force boundary.

The normalized quality is a geometric mean of the physical components and is
explicitly a diagnostic score, not a learned probability. Telemetry is off by
default and changes neither controller actions nor candidate rank.

## Fixed predictive windows

The final path samples the last physics substep at the 30 Hz controller rate.
It reports two 0.1 second windows, each containing three samples:

1. the last bilateral samples before the parcel first reaches 5 mm lift;
2. the first three loaded samples at or above 5 mm lift.

These windows are selected without looking at the later task result. Full
transport events remain diagnostic output, but are not used for the predictive
claim.

## Development results

On `4120001`, the successful centered `+45 mm` candidate had larger early
friction and disturbance reserves than the failed `+40 mm` candidate. This was
encouraging but insufficient: both early-loaded windows were classified robust
and their mean quality scores were 0.869 and 0.858.

The frozen `7130001` group disproved a simple threshold. Its three successes
and three failures produced overlapping values. One successful candidate had a
zero pre-lift robust fraction, while one later 100.70 N safety abort had a
pre-lift robust fraction of one. Early-loaded mean quality ranged from 0.710 to
0.900 for successes and 0.515 to 0.895 for failures. Therefore neither the
binary robust flag nor quality score has predictive validity for integration.

## ROCm scheduling result

A vectorized PyTorch implementation matched the pure Python reference to five
decimal places, but it was slower for approximately eight contact points per
sample. At 240 Hz telemetry, the two-rollout diagnostic changed from 93.98 s
with the reference path to 101.65 s with many small ROCm operations. Mean
metric latency changed from `6.84/4.06 ms` to `7.81/5.29 ms` for the two
rollouts. This is retained as a reproducible negative optimization result.

The final default uses the CPU reference scorer at 30 Hz while Genesis physics
and contact solving remain on the Radeon. Sampling reduction preserved the
metric direction, reduced the raw artifact from 14.3 MB to 6.0 MB, and reduced
the matched run to 86.66 s. A future online metric should batch contacts across
environments or control frames before moving this small calculation to ROCm.

## Reproduction

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

Use `--contact-wrench-backend rocm` only to reproduce the small-tensor backend
comparison. Compact evidence and raw artifact hashes are in
`evidence/expert/radeon-contact-wrench-development-v1.json`.
