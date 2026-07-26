# Mobile Bimanual VLA Status (2026-07-27)

## Verified pipeline

The mobile embodiment is a 21-DoF holonomic base with two Franka Panda arms. Its left arm carries
three physical suction-cup collision geometries and its right arm carries a V cradle. The successful
v41 expert episode used the left suction arm; cooperative dual-arm parcel support is not yet claimed.

On one AMD Radeon `gfx1100`, the v41 expert formed two cup seals on a 0.4 kg rigid parcel, lifted it
0.0811 m, transported it 0.30 m, placed it with 0.0118 m final error, and released it. The attachment
did not break. Peak compliant suction force was 11.84 N and peak cup contact was 2.37 N, below the
35 N task abort line.

## Audited dataset

The v43 LeRobotDataset contains one complete successful episode, 655 frames at 30 Hz, 224x224 RGB-D,
a 43-D non-privileged state, and a 19-D action. All six stages are present: 30 pregrasp, 191 approach,
90 lift, 224 transport, 90 place, and 30 release frames. The 7-D parcel pose is stored separately and
is not a policy input. Metric TIFF depth spans 2.61--20.00 m. Finite values, cadence, base speed,
quaternion norms, tool commands, depth units, and privileged-state isolation pass the dataset audit.

## SmolVLA training

LeRobot SmolVLA is initialized from the Apache-2.0
`HuggingFaceTB/SmolVLM2-500M-Video-Instruct` checkpoint. The mobile configuration has 450,061,536
total parameters and 99,896,352 trainable parameters, consumes RGB, 43-D state, and task text, and
produces 19-D base/dual-arm actions. Metric depth is recorded but is not an input to this checkpoint.

The 50-step Radeon pilot completed with AMP and a peak reported allocation of 1.79 GB. Mean loss was
2.4616 over steps 1--5 and 1.2410 over steps 46--50; the minimum was 1.088. This is a training-chain
pilot on one episode, not convergence or generalization.

## Six-stage checkpoint evaluation

The evaluator selects the middle frame of every audited stage, resets the policy action queue, and
uses fixed seeds `20260727`--`20260732`. All six calls returned finite 19-D actions. Warm inference
latency was 149.47 ms mean and 153.00 ms P95; mean stage MAE against the expert action was 0.1201.

Zero of six raw actions met the expert execution envelope. Cartesian targets were 0.054--0.469 m from
the current end-effectors, above the 0.04 m step limit, and the left suction command sign matched the
expert in only two of six stages. The safety executor made every action numerically executable by
bounding base speed, Cartesian steps, quaternions, and binary tool commands. This proves the ROCm
checkpoint interface, but it also rejects direct closed-loop use of this pilot.

## Decision and next gate

Do not run the 50-step checkpoint as the primary mobile controller. Freeze it as the undertrained
baseline. Next, collect parameterized successful and failed episodes across parcel size, mass,
friction, pose, and camera perturbations; balance all six stages; then train a multi-episode checkpoint.
Harness-Lite may evaluate bounded residual candidates only after offline action-envelope performance
improves. Promotion requires a disjoint closed-loop set with task success, force, drop, latency, and
per-profile metrics; no result from this single episode may be called mobile generalization.

## Reproduction

```bash
python scripts/audit_mobile_dataset.py \
  --dataset-root outputs/mobile-suction-dataset-v43/lerobot_dataset \
  --output outputs/mobile-suction-dataset-v43/audit.json

MOBILE_SMOLVLA_STEPS=50 bash scripts/train_mobile_smolvla_rocm.sh \
  outputs/mobile-suction-dataset-v43/lerobot_dataset \
  outputs/train/mobile-smolvla-full-episode-50step-v1

python scripts/smoke_mobile_smolvla_inference_rocm.py \
  --checkpoint outputs/train/mobile-smolvla-full-episode-50step-v1/checkpoints/000050/pretrained_model \
  --dataset-root outputs/mobile-suction-dataset-v43/lerobot_dataset \
  --output outputs/eval/mobile-smolvla-50step-six-stage-v1.json \
  --seed 20260727
```
