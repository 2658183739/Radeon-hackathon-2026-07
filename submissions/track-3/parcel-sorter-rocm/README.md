# Parcel Sorter ROCm

Latest mobile result: [Harness-Lite and failure-driven self-improvement](docs/MOBILE_HARNESS_SELF_IMPROVEMENT_2026-07-27.md), including a successful SmolVLA base-residual closed loop on one Radeon GPU.

Mobile extension: [43-D state / 19-D action SmolVLA status](docs/MOBILE_VLA_STATUS.md).
The v2 checkpoint was trained for 2,400 steps on six successful expert episodes. Harness-Lite
passed a 36-sample action-envelope ablation and controls bounded base residuals during grasp
approach and 30 cm transport. The early five-run gate achieved 4/5; a later independent
100-run baseline achieved 96/100 and was audited by the self-improvement cycle below. Broad
unseen-geometry generalization remains unverified.
The [resumable self-improvement cycle](docs/MOBILE_SELF_IMPROVEMENT_CYCLE.md) now connects
failure curriculum, Radeon retraining, paired 100-run frozen evaluation, and isolated
promotion; a candidate cannot replace the checkpoint without the 80%, safety, and ROCm gates.
The cycle has now completed: v2 scored 96/100 and bridge-trained v3 scored 91/100. v3 placed
successful parcels more precisely but failed Wilson non-inferiority, so it was isolated and
did not replace v2.
The [paired RGB-D ablation](docs/MOBILE_RGBD_ABLATION.md) verifies two-image SmolVLA training and
online control on ROCm. RGB-D completed one development task but regressed paired Harness MAE by
1.35% and added 9.65% offline latency, so the gate retained RGB and blocked a 100-trial campaign.
The [paired left-arm residual ablation](docs/MOBILE_ARM_RESIDUAL_ABLATION.md) executed bounded
SmolVLA arm-position residuals during transport. Baseline and candidate both scored 94/100 with
zero force violations and 2,306/0 accepted/rejected candidate IK updates, but mean placement
error increased from 1.40 cm to 2.45 cm. The preregistered gate rejected the mode, so v2 remains
base-residual only.

Parcel Sorter ROCm is an open-source Physical AI pipeline for small-parcel
picking and two-bin sorting on a single AMD Radeon GPU. It combines Genesis
rigid-body simulation, a Franka Panda manipulator, aligned RGB-D sensing,
closed-loop safety supervision, expert demonstration collection, LeRobot ACT
training, model-driven evaluation, video capture, and ROCm performance
measurement.

This directory is the Track 3 source submission. The primary reproduction path
uses AMD Radeon and ROCm. An NVIDIA development path is included for local
iteration, but CUDA results do not satisfy the competition execution
requirement.

## Verified system

The complete pipeline was executed on one Radeon device with the following
runtime:

| Component | Verified value |
| --- | --- |
| GPU target | AMD Radeon Graphics, `gfx1100` |
| VRAM | 47.98 GiB |
| Operating system | Ubuntu 24.04 |
| ROCm | 7.2.1 |
| PyTorch | 2.9.1 ROCm build |
| Genesis | 1.2.3 at the revision in `UPSTREAM_LOCK.json` |
| LeRobot | 0.6.1 at the revision in `UPSTREAM_LOCK.json` |
| Python | 3.12 |

PyTorch exposes a ROCm device through its CUDA-compatible Python API. For this
reason, `cuda:0` in the source denotes the single HIP/ROCm device and does not
mean that CUDA is used on the Radeon execution path. The preflight script
rejects a non-HIP PyTorch build.

## Implemented workflow

1. Genesis creates a randomized parcel-sorting scene with a Franka Panda,
   rigid parcels, two destination bins, an overhead RGB-D camera, joint state,
   end-effector pose, and gripper contact force.
2. A deterministic IK expert and a closed-loop state machine generate safe
   demonstrations. The supervisor verifies grasp contact, retries failed
   grasps, checks release and bin placement, and stops on excessive force.
3. Successful demonstrations are written as a LeRobotDataset. Every attempt,
   including failures, is retained as JSONL for audit and failure analysis.
4. A 52M-parameter ACT policy is trained from RGB and a 20-dimensional robot
   state. Ground-truth parcel pose is deliberately excluded from policy input.
5. ACT actions pass through finite-value, quaternion-normalization, Cartesian
   step-limit, gripper, IK, PD, and force-safety boundaries before execution.
6. The same Radeon runs physics, rendering, model training, model inference,
   and performance benchmarks.

The catalog v1 adds seven weighted training profiles, while catalog v2 expands
this to twelve balanced training strata and nine evaluation-only industry-size
boundary profiles (four existing profiles plus five newly sourced boundaries).
Both use Box/Cylinder geometry, stable profile-specific
episode IDs, and a stratified evaluator. Training ranges are explicitly marked
as Panda-aperture engineering strata; carrier dimensions carry official source
URLs and remain evaluation-only when the current gripper cannot grasp them.

See [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) for the design rationale,
results, limitations, and competition mapping.

Chinese versions and engineering-learning material are maintained alongside the
English submission documents:

- [README_CN.md](README_CN.md) and [TECHNICAL_REPORT_CN.md](TECHNICAL_REPORT_CN.md)
- [Optimization roadmap](docs/OPTIMIZATION_ROADMAP.md) / [中文](docs/OPTIMIZATION_ROADMAP_CN.md)
- [Engineering decision log](docs/ENGINEERING_DECISION_LOG.md) / [中文](docs/ENGINEERING_DECISION_LOG_CN.md)
- [Development journal](docs/DEVELOPMENT_JOURNAL.md) / [中文](docs/DEVELOPMENT_JOURNAL_CN.md)
- [Engineering playbook](docs/ENGINEERING_PLAYBOOK.md) / [中文](docs/ENGINEERING_PLAYBOOK_CN.md)
- [Implementation and optimization learning record](docs/IMPLEMENTATION_AND_OPTIMIZATION_RECORD.md) / [中文](docs/IMPLEMENTATION_AND_OPTIMIZATION_RECORD_CN.md)
- [Latest evidence-driven optimization session](docs/OPTIMIZATION_SESSION_2026-07-25.md) / [中文](docs/OPTIMIZATION_SESSION_2026-07-25_CN.md)
- [Model selection](docs/MODEL_SELECTION.md) / [中文](docs/MODEL_SELECTION_CN.md)
- [Research and open-model matrix](docs/RESEARCH_AND_MODEL_MATRIX.md) / [中文](docs/RESEARCH_AND_MODEL_MATRIX_CN.md)
- [RGB-D optimization record](docs/MULTIMODAL_OPTIMIZATION_2026-07-25.md) / [中文](docs/MULTIMODAL_OPTIMIZATION_2026-07-25_CN.md)
- [End-effector capability contract](docs/END_EFFECTOR_CAPABILITY.md) / [中文](docs/END_EFFECTOR_CAPABILITY_CN.md)
- [Project status and reproduction protocol](docs/PROJECT_STATUS.md) / [中文](docs/PROJECT_STATUS_CN.md)

- [Geometry-aware grasp-planning result](docs/GEOMETRY_AWARE_GRASP_PLANNING.md) / [Chinese](docs/GEOMETRY_AWARE_GRASP_PLANNING_CN.md)
- [Open-source parcel gripper adapter](docs/PARCEL_GRIPPER_ADAPTER.md) / [中文](docs/PARCEL_GRIPPER_ADAPTER_CN.md)

## Repository layout

```text
configs/                 Task, simulation, sensor, and randomization settings
docs/                    Architecture and supplementary documentation
scripts/                 Bootstrap, training, evaluation, video, and benchmarks
src/parcel_sorter/       Simulator integration and Physical AI application code
tests/                   Deterministic unit tests
Dockerfile.rocm          Pinned clean-build ROCm container definition
UPSTREAM_LOCK.json       Exact Genesis and LeRobot source revisions
TECHNICAL_REPORT.md      Track 3 technical report
TECHNICAL_REPORT_CN.md   Chinese technical report
docs/                    Paired architecture, optimization, and learning notes
```

Generated datasets, checkpoints, videos, and logs are intentionally excluded
from Git. They can be reproduced by the commands below and are recorded with
configuration and runtime provenance in their output directories.

## 1. Bare-metal ROCm setup

The host must expose exactly one supported Radeon device to the process and
provide a working ROCm PyTorch installation. On the competition image, the
ROCm PyTorch wheels may already be installed system-wide.

```bash
git clone <this-fork-url>
cd Radeon-hackathon-2026-07/submissions/track-3/parcel-sorter-rocm

bash scripts/preflight_radeon.sh
ROCM_PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
INSTALL_LEROBOT=1 bash scripts/bootstrap_radeon.sh
source scripts/activate_radeon_env.sh
```

The bootstrap downloads only the revisions listed in `UPSTREAM_LOCK.json`,
installs this project, runs ROCm and Genesis smoke tests, and executes the unit
test suite.

## 2. Deterministic end-to-end smoke run

```bash
bash scripts/run_pipeline_radeon.sh outputs/radeon-run
```

This executes the ROCm smoke test, three expert episodes, the robustness suite,
a parallel Genesis benchmark, and a generated report draft. For an individual
expert run with video:

```bash
python scripts/run_expert.py \
  --backend rocm \
  --episodes 10 \
  --record-video \
  --output outputs/expert-eval
```

The summary is written to
`outputs/expert-eval/expert/summary.json`; MP4 files are stored under its
`videos/` directory.

Compare a control change against the same episode indices:

```bash
python scripts/compare_expert_runs.py \
  --baseline evidence/expert/randomized-120-summary.json \
  --candidate outputs/expert-candidate/expert/summary.json \
  --output outputs/expert-candidate/comparison.json
```

The comparison rejects mismatched episode sets and reports recovered failures,
regressions, force-abort changes, throughput retention, and acceptance gates.

For a reset-pose diagnostic, keep the baseline configuration and override only
the nine-joint home pose. The override is copied into `summary.json`, so the
run remains auditable. Candidate poses are not accepted until a matched Radeon
experiment passes the task, safety, and throughput gates:

```bash
python scripts/run_expert.py \\
  --config configs/catalog_v2.toml --backend rocm \\
  --episodes 20 --start-episode 0 --profile large_narrow_carton \\
  --reset-qpos -1.0124 1.0 1.4 -1.6878 -1.5799 1.7757 1.4602 0.04 0.04 \\
  --output outputs/diagnostics/large-narrow-home-c
```

The fixed 20-episode Radeon acceptance protocol is also available as one
command. It refuses to reuse an output root, runs the baseline and pose-C
candidate with the same profile and randomization, compares both summaries,
and writes `SHA256SUMS`:

```bash
bash scripts/run_reset_pose_ab_rocm.sh \
  configs/catalog_v2.toml outputs/radeon-reset-ab-v1
```

Run one deterministic episode for every training parcel profile:

```bash
python scripts/evaluate_catalog.py \
  --backend rocm \
  --episodes-per-profile 1 \
  --output outputs/catalog-v1-smoke
```

Repeat `--profile <id>` to select strata. Evaluation-only carrier dimensions
require `--include-evaluation-only` and must not be mixed into training success.

Collect a targeted hard-example shard with catalog v2. Here `--episodes` means
episodes per selected profile, and each profile receives a separate episode
namespace. Use a new output directory for each shard:

```bash
python scripts/run_expert.py \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --episodes 20 \
  --start-episode 1000 \
  --profile micro_box \
  --profile upright_canister \
  --record-sensors --lerobot \
  --output outputs/catalog-v2-hard-shard
```

The audit writer refuses to overwrite an existing episode file. This makes
repeated collection explicit rather than silently corrupting provenance. Both
expert and learned-policy summaries include `profile_summaries` for matched
success, force, drop, latency, and throughput comparisons.

## 3. Collect an RGB-D LeRobotDataset

```bash
python scripts/run_expert.py \
  --backend rocm \
  --episodes 120 \
  --record-sensors \
  --lerobot \
  --output outputs/radeon-dataset-120
```

The policy dataset contains:

| Feature | Shape | Meaning |
| --- | --- | --- |
| `observation.images.overhead_rgb` | `3 x 224 x 224` | Overhead RGB image |
| `observation.images.overhead_depth` | `1 x 224 x 224` | Metric depth in metres |
| `observation.images.overhead_depth_rgb` | `3 x 224 x 224` | Fixed-range depth view for standard visual backbones |
| `observation.state` | `20` | Joints, end-effector pose, target, contact force |
| `observation.privileged_state` | `7` | Parcel pose for audit only; not used by ACT |
| `action` | `8` | Cartesian position, quaternion, gripper command |

Only successful episodes enter the LeRobot training dataset. Failed attempts
remain available in the JSONL audit data to support error analysis and future
hard-example collection.

Run the metadata gate before training. Historical `radeon-dataset-120-v1`
depth was accidentally scaled by `0.001`; it remains valid for the committed
RGB ACT baseline but must not be used for RGB-D. Newly collected shards include
the corrected metric depth and derived three-channel view.

```bash
python scripts/audit_dataset.py --dataset-root <lerobot_dataset>
python scripts/audit_dataset.py --dataset-root <lerobot_dataset> --require-depth-rgb
```

After collection is complete, freeze the train/validation/held-out split before
starting model comparison:

```bash
python scripts/build_dataset_split.py \
  --audit-root outputs/radeon-dataset-400-v2/expert/audit_dataset \
  --dataset-root outputs/radeon-dataset-400-v2/expert/lerobot_dataset \
  --output outputs/radeon-dataset-400-v2/dataset-split.json \
  --seed 20260725
```

The manifest stratifies by parcel profile, records original and LeRobot episode
IDs, and excludes held-out episodes from training. Pass the same manifest to
every matched run:

```bash
DATASET_SPLIT_MANIFEST=outputs/radeon-dataset-400-v2/dataset-split.json \
ACT_SEED=11 ACT_STEPS=30000 ACT_USE_AMP=true \
bash scripts/train_act_rocm.sh \
  outputs/radeon-dataset-400-v2/expert/lerobot_dataset \
  outputs/train/act-rgb-seed11
```

The Diffusion entry uses the same `DATASET_SPLIT_MANIFEST`. Do not regenerate
the manifest between seeds or between RGB and RGB-D comparisons.

## Reproducible model sweep

Run ACT first and keep models sequential on the single GPU:

    MODEL_SWEEP_MODELS=act MODEL_SWEEP_SEEDS=11,22,33 \
    bash scripts/run_model_sweep_rocm.sh \
      outputs/radeon-dataset-400-v2/expert/lerobot_dataset \
      outputs/radeon-dataset-400-v2/dataset-split.json \
      outputs/model-sweep/act

After the ACT gate passes, set MODEL_SWEEP_MODELS=act,diffusion to add the
compact Diffusion RGB/RGB-D comparison. The sweep records one CSV row and one
log per model/modality/seed; failed runs are retained and do not silently
alter later conditions.

On a cloud instance, the same sequence can be left as one auditable job:

    nohup bash scripts/watch_and_train_rocm.sh outputs/radeon-dataset-400-v2 \
      > outputs/radeon-dataset-400-v2/watch-and-train.log 2>&1 &

## 4. Train ACT on one Radeon

```bash
ACT_STEPS=5000 \
ACT_BATCH_SIZE=32 \
ACT_NUM_WORKERS=4 \
ACT_SAVE_FREQ=1000 \
ACT_USE_AMP=true \
ACT_IMAGE_TRANSFORMS=false \
bash scripts/train_act_rocm.sh \
  outputs/radeon-dataset-120/expert/lerobot_dataset \
  outputs/train/act-radeon-5000
```

The script validates ROCm and dataset metadata before training, keeps weights local, disables cloud
logging, reserves 10% of episodes for evaluation, and saves periodic
checkpoints. The default trains ACT from RGB and non-privileged robot state.
For a matched RGB-D experiment on a newly collected valid shard, add
`ACT_USE_DEPTH=true`; the checkpoint then consumes both RGB and the derived
depth view, and the generic evaluator discovers the second input automatically.

Generic image transforms default to off because synthetic manipulation labels
depend on precise geometry. Set `ACT_IMAGE_TRANSFORMS=true` only as a controlled
ablation with otherwise identical data, seeds, and checkpoint steps. The
committed 5,000-step evidence predates this change and was trained with generic
transforms enabled; no result is attributed to the new default yet.

To compare training precision and batch size on the target card:

```bash
bash scripts/benchmark_act_training_rocm.sh
```

## 5. Closed-loop learned-policy evaluation

```bash
python scripts/evaluate_policy.py \
  --checkpoint outputs/train/act-radeon-5000/checkpoints/004000/pretrained_model \
  --backend rocm \
  --episodes 10 \
  --start-episode 10 \
  --record-video \
  --output outputs/eval-act-4000-e10
```

`--start-episode` selects a deterministic, non-overlapping randomization range.
Use it to avoid evaluating every checkpoint only on episode zero. The summary
records the exact start, end, and count of evaluated episodes.

Rank multiple checkpoint summaries by closed-loop task performance:

```bash
python scripts/summarize_act_evaluations.py \
  outputs/eval-act-sweep \
  --output outputs/act-checkpoint-ranking.json
```

The tool rejects duplicate episode indices and ranks success before latency.

ACT is the verified learned baseline. Diffusion is the next controlled Radeon
comparison:

```bash
bash scripts/train_diffusion_rocm.sh <lerobot_dataset> outputs/train/diffusion-radeon

# Compact one-step smoke or later controlled ablation:
DIFFUSION_DOWN_DIMS=256,512,1024 DIFFUSION_HORIZON=32 \
DIFFUSION_N_ACTION_STEPS=8 DIFFUSION_INFERENCE_STEPS=10 \
bash scripts/train_diffusion_rocm.sh <lerobot_dataset> outputs/train/diffusion-compact
```

Diffusion is an implemented training path, not a measured capability claim. The
compact smoke is recorded in
`evidence/training/diffusion-compact-1step-rocm.md`; it reduced the model to
76.6M parameters and completed one Radeon step, but has not been selected by
closed-loop success. VLA-Adapter 0.5B remains an unintegrated comparison
candidate. The active VLA path uses LeRobot SmolVLA code (Apache-2.0)
initialized from `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` revision
`7b375e1b73b11138ff12fe22c8f2822d8fe03467` (Apache-2.0). The submitted 10k
checkpoint is trained locally on project-generated trajectories on one Radeon;
its trainer-generated `license` metadata is null, so the source manifest and
derived-checkpoint provenance must accompany any separately distributed
weights. The evaluator keeps it behind the same Genesis supervisor and 35 N
force boundary.

## 6. GPU simulation benchmark

```bash
python scripts/benchmark_parallel.py \
  --backend rocm \
  --env-counts 1,16,64,128 \
  --output outputs/benchmarks/parallel.json
```

For supporting evidence, capture `rocm-smi` alongside the benchmark and retain
the raw JSON, training log, and config used for each reported result.

## 7. Container build

The container pins ROCm 7.2.1, Ubuntu 24.04, Python 3.12, PyTorch 2.9.1, and
the two upstream source revisions. It does not depend on an untracked local
`third_party` directory.

```bash
docker build \
  -f Dockerfile.rocm \
  --build-arg INSTALL_LEROBOT=1 \
  -t parcel-sorter-rocm:rocm7.2.1 .

docker run --rm \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --ipc=host \
  --shm-size=16g \
  --security-opt seccomp=unconfined \
  parcel-sorter-rocm:rocm7.2.1
```

Nested Docker is not required on the competition cloud instance; the
bare-metal setup above is the validated primary path.

## Verified results and interpretation

| Measurement | Result |
| --- | ---: |
| Randomized expert evaluation | 96 / 120 successful episodes (80.0%) |
| Historical RGB/state demonstrations | 96 episodes, 11,753 frames; depth invalid for RGB-D |
| Fixed 10-seed expert baseline | 90.0% success, 0% drop rate |
| Fixed-seed expert throughput | 727 successful parcels/hour |
| ACT training | 5,000 steps, AMP, batch size 32 |
| ACT final evaluation loss | 0.1384 |
| ACT checkpoint 4,000, episodes 10-19 | 30.0% closed-loop success |
| ACT checkpoint 4,000 inference | 2.05 ms mean, 8.00 ms P95 |
| ACT checkpoint 5,000, episodes 10-19 | 10.0% closed-loop success |
| Parallel Genesis, 128 environments | 46,582 environment-steps/s |
| Peak observed GPU utilization | 83% |
| ACT training throughput, AMP batch 32 | 80 samples/s |
| Parcel-catalog regression smoke | 4 of 7 one-episode profiles complete; not a success rate |
| Deterministic unit suite | 71 passing tests on Radeon |

The 120-episode expert result is the primary capability measurement. The ACT
result proves that training, checkpoint reload, visual inference, and Genesis
closed-loop execution all run on ROCm, but the learned policy is not yet
converged. On the same episode range, the 4,000-step checkpoint outperformed
the 5,000-step checkpoint, so checkpoint selection must use task success rather
than offline loss alone. The principal current failure mode is excessive
contact force during fast approach; 22 of 24 failed expert episodes ended at
the configured safety boundary. These limitations are reported rather than
hidden. Raw summaries and logs are indexed in [evidence/README.md](evidence/README.md).

A matched 120-episode experiment with a fixed 0.01 m final-approach step was
rejected: success fell from 80.0% to 75.0%, force aborts rose from 22 to 25,
and throughput retention was 73.6%. The default therefore remains 0.04 m. The
separate setting is retained only as an experiment parameter; the next control
experiment will combine distance- and force-aware velocity shaping instead of
assuming that a fixed slowdown is sufficient.

The catalog's 0.01 m setting is not that rejected isolated candidate. It applies
only after a separate XY gate and latched descent, together with geometry-aware
pregrasp tolerance and lift-transfer-descend motion. In the final one-episode
smoke, four box profiles completed while the micro box and both cylinder
profiles remained explicit hard cases.

## Reproducibility and tests

The frozen experiment contract is `configs/campaign_v1.toml`. Validate it before
any remote run:

```bash
python scripts/validate_campaign.py configs/campaign_v1.toml
```

The contract fixes the ROCm device, one-GPU rule, 35 N safety limit, catalog
hash, evaluation episode IDs, seeds, training budgets, open-source declarations,
and acceptance gates. It intentionally leaves future dataset and split hashes
as `PENDING` until balanced RGB-D collection is complete.

`run_model_sweep_rocm.sh` validates this contract automatically before it starts
any ACT or Diffusion cell. Set `CAMPAIGN_PATH` only when replaying a new,
separately committed campaign version.

To aggregate an existing expert or policy summary by physical category:

```bash
python scripts/summarize_categories.py outputs/.../summary.json
```

```bash
source scripts/activate_radeon_env.sh
python -m unittest discover -s tests -q
```

The verified suite contains 56 tests covering configuration validation, domain
randomization, state-machine transitions, dataset contracts, metrics, runner
behaviour, parcel catalog scheduling and geometry, expert hysteresis and safe
transfer, safety limits, evaluation aggregation, and matched run comparison.
GPU tests and end-to-end
simulation are intentionally separate because they require Genesis assets and
a supported GPU runtime.

## Mobile bimanual development baseline

The current expansion target is a holonomic wheeled base with two Franka Panda
arms. `mobile_bimanual.py` transforms Genesis' Apache-2.0 Bi-Franka MJCF at
runtime, adds original planar `x/y/yaw` joints, a physical chassis, wheel
visuals, bounded navigation commands, deterministic dual-arm task allocation,
and semantic parcel routing. The upstream asset is not copied into this
repository.

On the competition Radeon, the generated 21-DoF robot compiled under Genesis
1.2.3 and moved 0.13047 m in a 240-step smoke while the simulator reported
roughly 494-516 FPS. A closed-loop obstacle route then reached its destination
in 321 control steps with 4.39 cm final error. A synchronized 14-arm-DoF IK
smoke reached both pregrasp targets within 1.60 cm, introduced no collision,
held base drift to 1.35 mm, and ran at 405 simulation FPS. Physical parcel
pickup and navigation-to-manipulation success are still pending and are not
claimed.

The optional hybrid-tool asset mounts three physical suction-cup collision
geometries on the left arm and a two-rail V cradle on the right arm. It
compiled and moved on Radeon at 454 FPS. A matched parallel-jaw long-parcel
probe pushed the parcel but did not establish bilateral contact, so that
failure is retained and the cooperative-lift claim remains closed.

`mobile_task.py` fixes the retraining contract at 19 actions: three bounded
base velocities and two eight-dimensional Cartesian/gripper commands. The
same module provides the fail-closed navigation, bilateral-contact, lift,
transport, placement, recovery, and force-abort state machine shared by the
future expert collector and SmolVLA policy.

```bash
python scripts/smoke_mobile_bimanual_rocm.py \
  --backend rocm --steps 240 --speed-m-s 0.20 \
  --output outputs/mobile-bimanual-smoke-v3
python scripts/smoke_mobile_bimanual_arms_rocm.py \
  --backend rocm --output outputs/mobile-bimanual-arms-v2
python scripts/smoke_mobile_bimanual_rocm.py --backend rocm --hybrid-tools \
  --output outputs/mobile-bimanual-hybrid-tools-v1
```

The raw result is tracked in
`evidence/mobile_bimanual/mobile-bimanual-smoke-v3.json`,
`mobile-navigation-v1.json`, `mobile-bimanual-arms-v2.json`,
`mobile-bimanual-hybrid-tools-v1.json`, and the retained
`mobile-bimanual-pick-v3-failure.json` negative result. The first successful physical suction lift
is `mobile-suction-lift-v40-success.json`.

## Development process

Development follows a fail-closed experiment loop: freeze episode IDs and
safety thresholds, record the baseline, change one causal mechanism, execute
matched Radeon runs, retain rejected candidates, and promote only after the
independent holdout gate. Current original changes include the parcel state
machine, geometry-aware planning, tri-cup suction physics, Harness-Lite
generator/verifier, failure-replay quarantine and promotion logic, parcel
classification, and the mobile bimanual embodiment. Detailed decisions and
failed experiments are retained under `docs/` and `evidence/`; successful and
unsuccessful results are both reported.

## Code provenance

Project-authored code is under `src/parcel_sorter`, `scripts`, and `tests` and
is MIT licensed. Runtime dependencies are fetched at locked revisions and are
not vendored. Genesis World and its Bi-Franka asset, LeRobot/SmolVLA code, and
the SmolVLM2 base checkpoint are Apache-2.0; exact repositories, revisions and
roles are listed in `THIRD_PARTY_NOTICES.md` and `UPSTREAM_LOCK.json`. The
mobile base, Harness-Lite rules, suction attachment, routing logic, experiment
orchestration, and generated datasets are project modifications, not an
unchanged upstream fork. Model weights are not committed to this repository.

## Licensing

Original project code is licensed under the MIT License. See
`THIRD_PARTY_NOTICES.md` and `UPSTREAM_LOCK.json` for dependency licenses,
source repositories, and exact revisions. No third-party source or model weight
is committed in this submission directory.

The Chinese operator guide is available in [README_CN.md](README_CN.md).
