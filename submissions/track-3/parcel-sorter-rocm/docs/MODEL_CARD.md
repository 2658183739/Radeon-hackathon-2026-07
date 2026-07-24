# Model Card: Parcel Sorter ACT Baseline

## Model

The baseline is a 52M-parameter ACT policy implemented by the pinned LeRobot
revision. It predicts 8-dimensional Cartesian/gripper actions in chunks from an
overhead RGB image and a 20-dimensional non-privileged state.

## Training

- Data: 96 successful simulated expert episodes, 11,753 RGB-D frames;
- Policy input: RGB and state; depth is not used in the baseline;
- Formal run: 5,000 steps, batch 32, AMP, 10% evaluation split;
- Checkpoints: every 1,000 steps;
- Execution hardware: one `gfx1100` Radeon, ROCm 7.2.1, PyTorch 2.9.1.

Generic image transforms now default to disabled. Any augmented model must be
reported as a separate matched experiment.

## Evaluation

| Checkpoint | Episode range | Success | Mean / P95 inference |
| --- | --- | ---: | ---: |
| 4,000 | 10-19 | 30% | 2.05 / 8.00 ms |
| 5,000 | 10-19 | 10% | 1.94 / 7.99 ms |

The 4,000-step checkpoint is the current measured choice because closed-loop
success has priority over final-step loss or small latency differences. Ten
episodes are still too few for a final model claim.

## Safety boundary

ACT cannot send raw torque. Outputs are checked for shape and finite values,
quaternions are normalized, Cartesian movement is bounded, and execution passes
through the deterministic task supervisor, IK, PD control, gripper semantics,
retry limits, and a hard contact-force abort.

## Intended use

- Demonstrating a complete ACT-on-ROCm training and inference path;
- controlled policy and modality ablations in the submitted simulator;
- education and research, not unattended physical deployment.

## Limitations

- Low closed-loop success and not converged;
- small simulated dataset and one task instruction;
- no depth input, real-world evaluation, calibration, or sim-to-real evidence;
- success can regress while offline loss improves;
- safety supervisor reduces risk but does not certify a physical robot system.

## Distribution

Publish weights with the exact code/config commit, data hash, checkpoint step,
training log, model configuration, upstream licenses, and SHA-256. Review the
pretrained visual backbone terms before assigning a final weight license.
