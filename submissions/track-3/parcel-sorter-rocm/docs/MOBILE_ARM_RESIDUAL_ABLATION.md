# Mobile SmolVLA Left-Arm Residual Ablation

## Question and scope

This experiment asks whether the selected SmolVLA v2 controller can actuate a left-arm
position residual during transport without regressing task success, safety, or placement
accuracy. It does not retrain the checkpoint or change suction, orientation, lift, place,
or release control, so the intervention is attributable to the anchored transport residual.

The robot has a three-DoF holonomic base and two seven-axis Franka Panda arms. The left arm
uses three physical compliant suction cups; the right V-cradle remains passive. SmolVLA runs
at 3 Hz and the Genesis physics and deterministic safety loop run at 240 Hz. Every rollout ran
on one AMD Radeon `gfx1100` with ROCm 7.2.1.

## Controller

The `base_residual` baseline lets SmolVLA contribute bounded base-velocity residuals during
grasp approach and transport. The `base_arm_residual` candidate preserves that path and adds
left-arm position residual execution during transport only:

- a base-relative moving expert anchor limits the cumulative position residual to 1 cm;
- orientation, suction, grasp, lift, place, and release remain expert-locked;
- Genesis IK runs at every 3 Hz policy update and rejects non-finite or failed solutions back
  to the expert joint target;
- the Harness-Lite base, Cartesian-step, residual, and 35 N force limits are unchanged.

This is real VLA-driven arm-position actuation, not full-action or cooperative dual-arm autonomy.

## Development gate

Seed `20260729` generated 12 outcome-blind parameter trials, three per profile. Baseline and
candidate both achieved 11/12; the same failure occurred before transport. The candidate
actuated the arm in all 11 transport-eligible trials, accepted 270 IK updates, rejected none,
and recorded no force violation. Mean successful placement error increased from 1.37 cm to
2.31 cm but remained inside the preregistered `+1 cm` development margin. This authorized a
new holdout and did not establish a generalization result.

## Frozen 100-trial protocol

After development was frozen, seed `20260730` generated 100 new trials, 25 each for
`small_carton`, `flat_mailer`, `electronics_box`, and `medium_carton`. Size, mass, friction,
and XY offset were randomized, with zero episode-ID overlap with development. Both conditions
used the same checkpoint, parameter order, 3 Hz policy rate, and four isolated workers.

Promotion required at least 80% candidate success, point and Wilson-lower-bound non-inferiority
within five percentage points, zero 35 N violations, arm actuation in every transport-eligible
candidate trial, accepted and zero rejected IK updates, one-Radeon/ROCm evidence in every trial,
and mean successful placement error no more than 1 cm above baseline.

## Results

| Metric | Base residual | Base + left-arm residual |
| --- | ---: | ---: |
| Success | 94/100 | 94/100 |
| Wilson 95% | 87.52%--97.22% | 87.52%--97.22% |
| Small carton | 25/25 | 25/25 |
| Flat mailer | 20/25 | 20/25 |
| Electronics box | 25/25 | 25/25 |
| Medium carton | 24/25 | 24/25 |
| Mean successful placement error | 1.40 cm | 2.45 cm |
| Maximum contact force | 16.50 N | 16.73 N |
| 35 N violations | 0 | 0 |
| Arm-actuated transport trials | 0 | 94/94 |
| Arm IK accepts/rejections | 0/0 | 2306/0 |

Paired outcomes were 94 both-success, six both-failure, zero recovery, and zero regression;
the exact two-sided McNemar result is `p=1.0`. Across the 94 common successes, placement error
increased by 1.0527 cm on average and 1.0868 cm at the median. All success, Wilson, safety,
actuation, IK, and single-Radeon checks passed, but the placement increase exceeded the 1 cm
margin by 0.0527 cm. The automatic result is `completed_not_promoted`.

## Decision

The selected controller remains SmolVLA v2 in `base_residual` mode. The margin must not be
relaxed after observing this result: the candidate recovered no failed task and consistently
reduced placement accuracy. A new study should collect transport segments with base motion and
end-effector perturbation recovery, explicitly balance arm-position losses, run a training-set
ablation, and then freeze a new parameter population rather than tune on this holdout.

This experiment does not establish right-cradle cooperation, unseen geometry, full-action VLA,
Sim-to-Real, or real-robot capability. Compact evidence, the frozen protocol, execution state,
and SHA-256 records are under `evidence/mobile_bimanual/arm_residual_v1/`.
