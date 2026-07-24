# Development and Experiment Journal

## Preface

This is an auditable engineering record, not a transcript of hidden chain of
thought. Each entry captures the problem, available evidence, alternatives,
decision rationale, code change, verification, and disposition. This follows
common ADR, experiment-tracking, and reproducible-research practice.

Status labels distinguish target-Radeon evidence, implemented but unmeasured
work, rejected experiments, and future proposals.

## 2026-07-24: parcel catalog and control revision

### 1. Replace one scaled box with an explicit catalog

The original randomizer could not reveal performance differences among flat,
long, cylindrical, and gripper-limit parcels. The selected design defines seven
weighted training profiles and four evaluation-only industry-size profiles.
Every 20-episode training block has an exact profile allocation, while
`sample_profile()` enables deterministic replay.

`ParcelProfileConfig`, stable block scheduling, profile-filtered evaluation,
and geometry tests were added. The catalog tests are part of the 48-test suite.
Decision: **keep**.

### 2. Implement real Box and Cylinder geometry

Representing tubes as boxes would make the capability claim invalid. A pure
`parcel_spawn_spec()` mapping now creates Genesis Box or Cylinder geometry.
Horizontal tubes rotate 90 degrees around Y and use radius for spawn height.
Decision: **keep**, verified by unit tests and Radeon runs.

### 3. Instrument the first failed catalog smoke run

All seven training profiles failed in the first catalog smoke. Instead of
attributing this to model size, frame traces were extended with force,
end-effector and parcel position, pregrasp/contact/lift booleans, and force-abort
state. This localized failure to approach, contact, lift, transfer, or abort.
Decision: **keep the diagnostics**.

### 4. Separate horizontal approach tolerance and latch final descent

One 3-D tolerance caused premature transitions and threshold oscillation. The
system now uses a 15 mm XY alignment tolerance and latches final descent after
alignment. Deterministic tests cover both behaviors. This enabled successful
smokes for small, flat, long, and near-limit boxes. Decision: **keep**.

### 5. Make pregrasp tolerance geometry-aware

Large non-flat boxes use a 35 mm pregrasp window, while flat parcels retain a
10 mm precision window. The rule is computed from geometry rather than profile
names. Tests and large-box smokes passed. Decision: **keep**.

### 6. Use lift-transfer-descend instead of a diagonal transfer

Diagonal motion reduced table and bin clearance. The new path first lifts to a
safe height, moves horizontally above the destination, then descends. This also
creates clearer failure stages. Box paths and force behavior improved.
Decision: **keep**.

### 7. Record cylinder grasp experiments

Aligning horizontal-tube grasp yaw directly to spawn yaw caused a 46.1 N abort
and was rejected. Perpendicular-axis grasp limited force to about 12.71 N but
still lost the tube during lift.

For the upright canister, additional clearance of 30 mm produced about 14 N and
no contact; 15 mm produced about 27.3 N without stable contact; 8 mm produced
about 29.3 N without stable dual-finger contact. The 8 mm and perpendicular-axis
settings remain the safest current geometry baseline. Further single-episode
hand tuning was stopped in favor of more data, learned control, or a different
end effector.

### 8. Final 20-second one-episode-per-profile smoke

| Profile | Success | Terminal stage | Retries | Peak force |
| --- | ---: | --- | ---: | ---: |
| `micro_box` | no | approach | 2 | 13.56 N |
| `small_carton` | yes | complete | 0 | 10.71 N |
| `flat_box` | yes | complete | 0 | 9.36 N |
| `long_box` | yes | complete | 0 | 11.60 N |
| `upright_canister` | no | abort | 2 | 29.30 N |
| `mailing_tube` | no | abort | 2 | 12.71 N |
| `near_limit_box` | yes | complete | 0 | 5.55 N |

This is a regression smoke, not a success-rate claim. The box improvements are
kept; micro-box and cylinder failures enter the hard-example queue. Formal
reporting requires multiple seeds per profile.

## Model and perception decisions

ACT remains the verified connectivity baseline. Diffusion is the conventional
multimodal-action comparison, and SmolVLA is the lightweight language-conditioned
route. All three use the same supervisor and execution safety path.

Current learned input is RGB, 20-D state including force, and task text for
SmolVLA. Metric depth is recorded but must not be silently treated as RGB. A
depth encoder or fusion change requires a matched ablation before it is claimed.

The first one-step Diffusion smoke stopped before model creation because the
optional `diffusers` dependency was absent. The bootstrap now installs LeRobot's
`training,diffusion,smolvla` extras and each training entry performs a dependency
preflight. The repeated smoke created a 264M-parameter model, completed one
forward/backward update on Radeon, and saved a checkpoint. This validates only
the training path.

SmolVLA dependency import succeeded, but probing `lerobot/smolvla_base` failed
because the instance could not reach Hugging Face. The entry point now requires
`SMOLVLA_POLICY_PATH`, favoring an offline-staged open checkpoint and allowing a
Hub ID only when network access exists. Status: entry ready, base not staged,
training not run.

## Capability map

The codebase now demonstrates validated configuration contracts, deterministic
catalog scheduling, Box/Cylinder physics, geometry-aware expert control,
closed-loop safety and recovery, multimodal dataset writing, ACT training and
inference, generic LeRobot checkpoint evaluation, and Radeon profiling.
Diffusion has a one-step path smoke; SmolVLA remains unmeasured pending its base.

## Workflow for the next change

Start from one measurable failure; freeze baseline episodes and safety limits;
change one major variable; run unit, single-episode, then multi-seed tests;
separate task, safety, latency, and throughput; record keep/reject/repeat; and
commit code, config, evidence, and paired documentation together.
