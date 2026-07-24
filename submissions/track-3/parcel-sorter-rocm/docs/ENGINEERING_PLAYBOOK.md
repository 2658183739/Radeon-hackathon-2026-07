# Engineering Playbook

This playbook turns the project into a reproducible, auditable workflow for learning and further optimization. It records observable evidence, code capabilities, decisions, and validation criteria; it does not expose hidden chain-of-thought. Every new experiment should follow the same structure and be mirrored in the Chinese document.

## 1. Fix the objective and boundaries first

The objective is to run simulation, sensing, policy inference, and closed-loop action execution on one AMD Radeon GPU with ROCm, and to pick, move, and sort parcels into two bins. The mainline is Franka Panda + Genesis + RGB/RGB-D + ACT, with a deterministic safety controller remaining downstream of every learned policy.

The following must not be presented as completed capabilities: a learned policy without fixed held-out evaluation, a Diffusion run that only has a one-step training smoke test, a VLA that has not passed license and ROCm audits, suction or cradle scenarios without the corresponding end effector, and the not-yet-implemented ROS 2 bridge.

Use three explicit states for every capability:

| State | Meaning | Allowed wording |
| --- | --- | --- |
| Verified | Repeatedly passes in the locked environment and episode set | “Verified on Radeon” |
| Pipeline smoke | Interfaces, training, or loading run, but task capability is unproven | “Pipeline smoke completed” |
| Planned/boundary | Not implemented or below an acceptance gate | “Planned/currently unsupported” |

## 2. Standard procedure for every change

### Step A: Ask one measurable question

Start from a failed trajectory or performance measurement, such as a collision during tube approach, an inconsistent depth unit, or excessive ACT P95 latency. Do not start from a model name, and do not change physics, data, and model layers simultaneously.

### Step B: Establish a replayable baseline

Freeze the Git commit, configuration, environment versions, single-device selection, random seed, episode list, safety threshold, and output directory. Save raw JSON, logs, a configuration copy, and SHA-256 hashes.

### Step C: Write contracts and tests

Before changing implementation, express inputs, outputs, units, shapes, valid ranges, error codes, and safety conditions as code contracts. Add unit tests first, then a single-episode smoke test, and only then run a multi-episode experiment.

### Step D: Change one primary variable

For example, change only `final_approach_step_m` or only `ACT_USE_DEPTH`. Keep the split, seeds, budget, and evaluation episodes unchanged. If multiple variables must change, split them into independent experiments and explain why.

### Step E: Gate on four metric families

Every candidate reports:

1. Task: total success, first-attempt success, retry recovery, drops, and per-profile results;
2. Safety: peak contact force, 35 N aborts, and whether execution continued after a violation;
3. Performance: mean/P95 inference latency, training throughput, peak VRAM, and GPU utilization;
4. Reproducibility: command, environment, seed, dataset-manifest hash, checkpoint hash, and log path.

A throughput gain that degrades task success or safety is rejected. Small samples report numerators, denominators, and Wilson 95% intervals, not percentages alone.

### Step F: Record keep, reject, or hold

Update both language logs immediately. Record the reason, failed evidence, and next step. Failed results are retained under `evidence/` as negative controls and are never silently overwritten.

## 3. Current code capability map

| Capability | Code location | Current validation | Next enhancement |
| --- | --- | --- | --- |
| Configuration and range checks | `src/parcel_sorter/config.py` | TOML, frozen configuration, invalid-range tests | Add configuration versions and migration checks |
| Randomization and episode scheduling | `randomization.py`, `episode_plan.py` | Stable seeds and profile strata tests | Record distribution summaries for each random variable |
| Genesis physics | `genesis_env.py`, `runner.py` | Box/Cylinder, Franka, two-bin sorting | V-shaped cradle, positioning slot, and richer materials |
| Sensor data | `dataset.py`, `data_quality.py` | RGB, metric depth, state, contact force | RGB-D alignment, point-cloud cache, and occlusion flags |
| Expert control | `expert.py`, `state_machine.py` | IK/PD, contact confirmation, retry, release checks | Failure recovery and end-effector switching |
| Safety supervision | `policy.py`, `contracts.py` | Finite values, quaternions, step limits, 35 N abort | Joint speed/acceleration and collision-energy gates |
| Dataset split | `dataset_split.py`, `build_dataset_split.py` | Fixed seed, profile stratification, held-out isolation | Machine-readable summaries and signatures |
| ACT | `train_act_rocm.sh`, `evaluate_act.py` | Radeon train/save/load/closed-loop interface | Three-seed RGB vs RGB-D held-out comparison |
| Diffusion | `train_diffusion_rocm.sh` | Lightweight one-step smoke | Matched 5/10/20 denoising evaluation |
| ROCm performance | `preflight_radeon.sh`, `benchmark_*` | HIP gate, AMP, parallel simulation | Stage profiling and eager/compile comparison |
| VLA | `train_smolvla_rocm.sh` | Compatibility entry only | Recursive license, operator, and offline-weight gates |
| ROS 2 | Reserved boundary | Not implemented | Optional bridge after simulator-policy contracts stabilize |

## 4. Optimization order and rationale

1. **Data quality first.** Collect at least 300 successful, profile-balanced RGB-D episodes; otherwise model comparisons measure sampling bias.
2. **ACT before Diffusion/VLA.** ACT is smaller and faster and provides the reproducible mainline. Diffusion is a multimodal action baseline; VLA is only a candidate for high-level semantic routing.
3. **Keep safety deterministic.** The policy outputs eight-dimensional Cartesian actions. IK, PD, gripper phases, and force limits remain in the supervisor so the model cannot emit unsafe torques directly.
4. **Use matched RGB-D ablations.** Compare RGB and RGB-D with identical manifests, seeds, budgets, and closed-loop episodes. Keep depth only if success improves without safety or latency regression.
5. **Fix physics before controller tuning.** Sampling dimensions, radii, friction, and solver scope must be correct before control tuning; controller parameters must not conceal geometry errors.
6. **Measure before ROCm tuning.** Profile simulation stepping, rendering, host-to-device transfer, and network inference separately before choosing AMP, batch, compilation, or caching changes.
7. **Add VLA, point clouds, and ROS 2 last.** They add dependency, license, and deployment risk and should wait until the mainline passes task and safety gates.

## 5. Experiment record template

Each experiment should include:

```text
ID / date:
Question and failure evidence:
Baseline commit, config, environment, and data manifest:
Candidate options:
Primary variable changed:
Task, safety, and performance metrics:
Command and output paths:
Outcome: keep / reject / hold:
Decision rationale:
Revisit condition and next step:
```

Store structured results as JSON/CSV and the explanation in `DEVELOPMENT_JOURNAL.md` and the corresponding decision log. This supports both human learning and automated report generation.

## 6. Reproduction and release gates

Run, in order:

```bash
bash scripts/preflight_radeon.sh
python -m unittest discover -s tests -q
python -m compileall -q src scripts
python scripts/audit_dataset.py --dataset-root <dataset> --require-depth-rgb
python scripts/build_dataset_split.py --audit-root <audit> --dataset-root <dataset> \
  --output <split.json> --seed 20260725
MODEL_SWEEP_MODELS=act MODEL_SWEEP_SEEDS=11,22,33 \
  bash scripts/run_model_sweep_rocm.sh <dataset> <split.json> <output>
```

The final submission includes source, configuration, Dockerfile, version locks, bilingual READMEs, technical report, dataset card, model card, experiment logs, and reproduction commands. Large datasets and weights stay out of Git; provide download instructions, hashes, and license evidence instead.

## 7. How to study the project

Read `PROJECT_STATUS.md` for the current boundary, then `DEVELOPMENT_JOURNAL.md` to see how failures drove code changes, and finally `ENGINEERING_DECISION_LOG.md` for the concrete decision records. For every module, answer three questions: what is the input contract, how is failure observed, and how is the result reproduced?

