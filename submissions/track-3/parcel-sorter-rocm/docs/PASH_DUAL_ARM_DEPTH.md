# PASH Dual-Arm Geometry Harness

## Scope

This extension gives the frozen RGB SmolVLA bounded authority over both arm
positions during parcel transport. It does not change VLA weights online, tool
commands, end-effector orientations, grasp, lift, placement, release, or the
35 N hard-force limit.

The design combines two system-level ideas:

- a Harness-style planner keeps deterministic primitives and safety gates in
  charge while exposing the VLA as a bounded action primitive; and
- an InSight-style primitive-gap loop records successful recoveries as
  retraining candidates, but only after RGB-D/action dataset audit.

Harness VLA is referenced from its primary project and paper
([project](https://harnessvla.github.io/),
[arXiv:2607.08448](https://arxiv.org/abs/2607.08448)). InSight is currently a
design reference only; its primary bibliographic metadata must be verified
before manuscript submission.

## Decision record

1. **Keep RGB SmolVLA as the semantic policy.** The paired RGB-D checkpoint was
   operational but regressed action MAE and latency, so it remains rejected.
2. **Use depth as a deterministic geometry sidecar.** A central metric-depth
   region produces sensor-quality and near-camera-occlusion scale caps.
   Missing, malformed, or mostly invalid depth fails closed to expert
   authority. This is not a robot-obstacle distance estimator.
3. **Project two arm proposals before IK.** Left/right residuals are decomposed
   into common and differential components. Common motion is bounded to 10 mm.
   Differential motion is bounded to 1.5 mm for independent handling and forced
   to zero when tri-suction and the V-cradle share a rigid parcel.
4. **Fade learned arm authority before placement.** Authority is full beyond
   120 mm remaining transport distance and reaches zero at 25 mm. Placement and
   release remain deterministic.
5. **Solve both arms together.** A single multi-link IK request validates the
   projected targets. Non-finite or failed IK discards the update.
6. **Integrate with episodic memory.** Cooperative tasks may select
   `pash_dual_arm`. A force event permits only expert recovery; suction, lift,
   placement, or release failures remove learned arm authority on the next
   attempt.

## Single-Radeon mechanism result

The retained run used one `gfx1100` Radeon with ROCm 7.2.1, PyTorch 2.9.1 ROCm,
Genesis 1.2.3, and the frozen 2,400-step RGB SmolVLA v2 checkpoint. It handled
one fixed `1.44 x 0.12 x 0.18 m`, 0.40 kg rigid carton.

| Metric | Result |
| --- | ---: |
| Full task | pass |
| Lift | 8.53 cm |
| Transport | 30 cm |
| Final placement error | 3.19 cm |
| Suction breaks | 0 |
| Peak suction/contact force | 27.03 / 14.90 N |
| Peak V-cradle contact force | 30.68 N |
| VLA calls | 67 at 3 Hz |
| Warm mean / P95 inference | 203.22 / 210.52 ms |
| Dual-arm IK updates | 24 accepted |
| Material left/right updates | 24 / 24 |
| Dual-arm residual physics steps | 2,356 |
| Maximum tool-separation change | 0 m |
| Force-Memory tightenings | 11 |
| Depth fail-closed events | 0 |
| Emergency stops | 0 |

The depth cap remained `1.0` because this scene had valid depth and no near-camera
occluder. That is the expected no-intervention result, not evidence that the
depth gate is unnecessary. Unit tests separately cover missing depth and
near-plane occlusion.

## Reproduction

```bash
source /workspace/rdna/bin/activate
export HIP_VISIBLE_DEVICES=0
export PYTHONPATH=/workspace/parcel-sorter-opt-v1/src
python scripts/evaluate_mobile_suction_lift_rocm.py \
  --backend rocm \
  --output outputs/pash-dual-arm-depth-v1 \
  --parcel-profile extra_long_carton \
  --parcel-size-m 1.44 0.12 0.18 \
  --parcel-mass-kg 0.40 \
  --parcel-friction 0.90 \
  --cooperative-cradle \
  --smolvla-checkpoint outputs/train/mobile-smolvla-mass-aware-b8w4-2400step-v2/checkpoints/002400/pretrained_model \
  --policy-mode base_dual_arm_residual \
  --policy-hz 3 \
  --force-memory-harness \
  --depth-risk-sidecar
```

Evidence is under `evidence/mobile_bimanual/dual_arm_depth_v1/`.

## Claim boundary

This is one deterministic mechanism case. It proves that both learned arm
residuals, depth-sidecar telemetry, Force Memory, multi-link IK, tri-suction,
and V-cradle contact ran together on one Radeon without crossing the registered
safety gates. It is not a success rate, unseen-geometry result, retry-benefit
estimate, learned visual-classification result, or sim-to-real result.
