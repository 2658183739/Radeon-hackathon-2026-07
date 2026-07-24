# Implementation and Optimization Record

Chinese companion: [IMPLEMENTATION_AND_OPTIMIZATION_RECORD_CN.md](IMPLEMENTATION_AND_OPTIMIZATION_RECORD_CN.md)

## Purpose and disclosure

This learning-oriented record explains observable engineering evidence, module
responsibilities, alternatives, decisions, validation, and the next experiment.
It does not expose private chain-of-thought or turn a plan into a result.

The project follows reproducible robotics and ML practice: configuration as
code, immutable data and evaluation manifests, contract-first implementation,
one primary variable per experiment, artifact hashes, held-out closed-loop
evaluation, and a deterministic safety layer outside the learned policy.

| State | Meaning | Permitted claim |
| --- | --- | --- |
| Verified | Repeatedly executed under the recorded Radeon environment | "Verified on Radeon" |
| Pipeline smoke | Interfaces execute but task quality is unproven | "Pipeline smoke completed" |
| Planned / gated | Not implemented or blocked by an explicit prerequisite | "Planned" or "compatibility-gated" |

## System capability map

| Layer | Code responsibility | Current state | Important boundary |
| --- | --- | --- | --- |
| Experiment contract | `config.py`, TOML catalogs, `contracts.py` | Verified | Invalid ranges and unsupported end effectors fail early |
| Episode generation | `randomization.py`, `episode_plan.py` | Verified | Stable seeds and profile namespaces prevent audit collisions |
| Physics and sensing | `genesis_env.py` | Verified | Genesis, Panda, Box/Cylinder, RGB-D, proprioception, contact force |
| Expert and supervisor | `expert.py`, `state_machine.py`, `runner.py` | Verified as a baseline | IK/PD and 35 N safety stay outside learned models |
| Dataset integrity | `dataset.py`, `data_quality.py`, `dataset_split.py` | Verified | Only successes enter LeRobot; depth must be metric metres for RGB-D |
| New collection planning | `collection_plan.py`, `plan_balanced_collection.py` | Implemented; Radeon execution pending | History estimates budget only; it never fills a new-shard quota |
| Imitation learning | `train_act_rocm.sh`, LeRobot ACT | Pipeline smoke | Current 190 successes do not clear the balanced-data gate |
| Diffusion | `train_diffusion_rocm.sh` | One-step smoke | No matched closed-loop capability claim |
| VLA / ROS 2 | compatibility scripts and research matrix | Gated / planned | License, ROCm operator, data, and closed-loop gates remain open |
| Radeon execution | preflight, bootstrap, benchmark and sweep scripts | Verified for the base stack | One visible AMD Radeon GPU and ROCm HIP are mandatory |

## Engineering history and decisions

### 1. Use a layered robot system, not a single large model

**Decision.** Genesis + Franka Panda provide physics and actuation; a deterministic
state machine owns phases and safety; ACT is the compact learned baseline. A
policy emits an eight-dimensional Cartesian action, while finite-value checks,
quaternion normalization, Cartesian limits, IK, PD, gripper phases, and the
35 N abort remain outside it.

**Reason.** Contact handling, motion limits, and recovery remain testable even
when learned-policy behavior is incomplete.

**Verification.** Expert rollouts, ACT train/save/load, and a learned-policy
closed-loop interface have executed on one Radeon. Learned task performance
remains smoke-only until matched held-out evaluation exists.

### 2. Repair simulation correctness before control tuning

**Observation.** Horizontal-cylinder sampling once used inconsistent radius and
spawn height, and an early gripper orientation closed along the wrong tube axis.

**Decision and reason.** Correct primitive dimensions, radius-derived placement,
and finger-axis alignment before changing controller gains or safety thresholds.
A controller tuned around invalid geometry would produce misleading results.

**Verification.** Geometry/catalog tests cover Box/Cylinder mappings. Causal
evidence and rejected candidates remain in `OPTIMIZATION_SESSION_2026-07-25.md`.

### 3. Scope local optimizations to local failure modes

**Observation.** Global three-frame grasp stabilization improved one tube contact
case but regressed several box profiles.

**Decision and reason.** Keep one global stability frame and enable three only
for tube profiles. Rolling physics and material changes follow the same rule so
one object class cannot silently change the baseline for unrelated objects.

**Verification.** The catalog regression recovered the 8/12 diagnostic completion
pattern. It is a regression smoke, never a success-rate claim.

### 4. Repair data semantics before multimodal learning

**Observation.** Historical depth had an incorrect scale and an implausible
metre median.

**Decision.** Preserve historical RGB/state data for reproducibility, reject it
for RGB-D, and collect new shards with raw float32 metre depth plus deterministic
depth visualization.

**Reason and verification.** Silent conversion would be unauditable.
`data_quality.py` gates RGB-D training on shape, metadata, metre units, and
plausible depth statistics.

### 5. Freeze data and evaluation before model comparison

**Decision.** A profile-stratified manifest maps original audit IDs to LeRobot
successful-episode IDs. ACT and Diffusion use the same train/validation/held-out
lists; checkpoint comparisons also require matching episodes and safety limits.

**Reason.** Different splits, episodes, or safety thresholds make model ranking
meaningless. Aggregate success can also conceal failure on a difficult profile.

**Verification.** Split/comparison code rejects incomplete collections, leakage,
mismatched evidence, and unsupported schemas. It reports per-profile outcomes,
Wilson intervals, drops, force, and latency.

### 6. New decision: collect a clean balanced shard

**Evidence.** The completed Radeon collection has 400 audited episodes but only
190 successful LeRobot episodes. The result is profile-imbalanced and below the
formal data gate.

**Alternatives.** Train immediately, append into the old LeRobot dataset, or
create a clean balanced shard guided by audit history.

**Decision.** Create an independent dataset with 30 successful RGB-D episodes
for each of 12 training profiles: 360 successes total. History estimates effort
only; it does not credit the new target. The current writer intentionally avoids
unsafe append semantics that could change ordering and provenance.

**Code capability.** `plan_balanced_collection.py` fingerprints
`audit_dataset/episodes.jsonl`, computes per-profile outcomes, and writes a
versioned plan. `run_expert.py --collection-plan` consumes its frozen,
profile-specific budgets in one clean writer session.

**Planning algorithm.**

```text
Wilson lower bound = conservative 95% lower confidence bound of past success
planning rate      = max(Wilson lower bound, configured planning-rate floor)
requested attempts = ceil(target new successes / planning rate * oversampling factor)
```

The floor prevents an unbounded request after zero historical success; it is a
scheduling guard, not a success guarantee. A profile remains
`requires_expert_diagnostic` while its Wilson lower bound is below the readiness
threshold. Bulk collection rejects such a plan unless explicitly acknowledged
as a diagnostic run.

**Reason.** The greatest current limitation is low-quality, uneven expert data,
not model size. This prevents more low-quality data for unresolved hard profiles
such as `large_narrow_carton`, `mailing_tube`, `upright_canister`, and
`medium_carton`.

**Verification.** Unit tests cover conservative planning, fresh-shard targets,
unready-plan rejection, acknowledgement behavior, profile-specific budgets,
duplicate profile rejection, and deterministic namespaces. Radeon execution is
still pending before this becomes a collection result.

## Immediate Radeon workflow

Run from the project root. The activation script checks the project `.venv`
before legacy cloud paths; do not assume `/workspace/rdna` exists.

```bash
cd /workspace/parcel-sorter-opt-v1
source scripts/activate_radeon_env.sh
export PYTHONPATH="$PWD/src"

python -m unittest discover -s tests -q

python scripts/plan_balanced_collection.py \
  --config configs/catalog_v2.toml \
  --audit-manifest outputs/radeon-dataset-400-v2/expert/audit_dataset/episodes.jsonl \
  --output outputs/radeon-balanced-v3/collection-plan.json
```

Read `summary.blocked_profiles` in the plan. For each blocked profile, run a
short isolated expert diagnostic after changing only one control or physics
factor. Do not use `--lerobot` for an untrainable diagnostic shard.

```bash
python scripts/run_expert.py \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --episodes 10 \
  --start-episode 5000 \
  --profile mailing_tube \
  --record-sensors \
  --output outputs/diagnostics/mailing-tube-v1
```

Regenerate the plan after diagnostics pass the selected readiness gate. Only
then start a new balanced training shard:

```bash
python scripts/run_expert.py \
  --config configs/catalog_v2.toml \
  --backend rocm \
  --collection-plan outputs/radeon-balanced-v3/collection-plan.json \
  --record-sensors --lerobot \
  --output outputs/radeon-balanced-v3

python scripts/audit_dataset.py \
  --dataset-root outputs/radeon-balanced-v3/expert/lerobot_dataset \
  --require-depth-rgb

python scripts/build_dataset_split.py \
  --audit-root outputs/radeon-balanced-v3/expert/audit_dataset \
  --dataset-root outputs/radeon-balanced-v3/expert/lerobot_dataset \
  --output outputs/radeon-balanced-v3/dataset-split.json \
  --seed 20260725
```

`--allow-unready-collection` is intentionally absent from the full-collection
command. It is an acknowledgement for a labeled diagnostic, not a normal way to
bypass data quality.

## Ordered optimization program

| Priority | Hypothesis / change | Fixed conditions | Acceptance rule | Do not do |
| --- | --- | --- | --- | --- |
| P0 | Diagnose high-force expert failures by phase, geometry, friction, contact trace | Same profile, episode IDs, 35 N | Lower force aborts without lower success or throughput | Raise the force threshold |
| P0 | Produce a new 12-profile balanced RGB-D shard | Separate output root and fixed catalog | At least 30 successes per training profile | Append ambiguously to old data |
| P1 | ACT RGB vs RGB-D late fusion | Same split, seeds 11/22/33, budget | Better held-out task result without safety/latency regression | Compare different splits |
| P1 | Compact Diffusion vs ACT | Same data, wrapper, held-out episodes | Better macro-profile success with usable P95 latency | Treat one-step smoke as capability |
| P1 | Curriculum and hard-example aggregation | Full-range held-out benchmark fixed | Better full-range performance | Narrow the benchmark |
| P2 | Profile render, conversion, transfer, inference, IK, physics | Synchronized timing, one GPU | At least 15% end-to-end gain, no task regression | Report enqueue time as latency |
| P2 | AMP / BF16 / `torch.compile` matrix | Same model/data/evaluation | No NaNs; same safety; memory and speed recorded | Change precision and architecture together |
| P3 | VLA-Adapter high-level routing | License and ROCm operator audits | Measurable instruction value; ACT/safety own continuous control | Replace the safety controller |
| P3 | Suction, cradle, point cloud, ROS 2 | Versioned hardware/control contract | Tool-specific closed-loop safety report | Claim unsupported hardware |

## Record template for every next change

Create paired English/Chinese entries in the development and decision logs. Keep
raw JSON, CSV, and logs under `evidence/` or a new output directory.

```text
ID and date:
Question and failure evidence:
Baseline commit, config, runtime, manifest hash, and episode IDs:
One primary changed variable and alternatives rejected:
Code contract added or modified:
Task, safety, performance, and uncertainty metrics:
Exact command and artifact paths:
Decision: keep / reject / hold:
Reason and revisit trigger:
```

This record, the [Engineering Playbook](ENGINEERING_PLAYBOOK.md), and raw
evidence are the project source of truth. Reports and videos should cite the
result state and artifacts, not replace them with unrepeatable narration.
