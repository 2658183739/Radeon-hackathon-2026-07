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
multimodal-action comparison. VLA-Adapter 0.5B is the preferred future
language-conditioned compatibility study after license and ROCm gates. Every
admitted policy uses the same supervisor and execution safety path.

The historical baseline uses RGB and a 20-D state including force. Corrected
shards also expose a deterministic depth view, whose ACT train/load/inference
path has passed a smoke test. A capability claim still requires a matched RGB
versus RGB-D ablation. Task text is reserved for admitted VLA candidates.

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
training not run. This was later superseded by the checkpoint-license audit:
the entry remains historical compatibility code and is not in the strict-open
submission path.

## Capability map

The codebase now demonstrates validated configuration contracts, deterministic
catalog scheduling, Box/Cylinder physics, geometry-aware expert control,
closed-loop safety and recovery, multimodal dataset writing, ACT training and
inference, generic LeRobot checkpoint evaluation, and Radeon profiling.
Diffusion has a one-step path smoke. VLA-Adapter remains a gated research
candidate, and SmolVLA is excluded from the strict-open result path.

## Workflow for the next change

Start from one measurable failure; freeze baseline episodes and safety limits;
change one major variable; run unit, single-episode, then multi-seed tests;
separate task, safety, latency, and throughput; record keep/reject/repeat; and
commit code, config, evidence, and paired documentation together.

## 2026-07-24: balanced collection and compact Diffusion

### Record 13: catalog v2 and targeted data collection

**Problem.** Catalog v1 under-represented medium cartons and could not directly
collect only known hard profiles. **Alternatives.** Keep the old mixture, use
manual config copies, or add a balanced catalog plus a deterministic profile
plan. **Decision.** Add twelve training strata in an exact 20-slot mixture and
repeatable `--profile` collection/evaluation. Carrier dimensions remain sourced,
evaluation-only boundaries. **Code.** Added `catalog_v2.toml`, `episode_plan.py`,
profile-aware expert/policy loops, and overwrite protection. **Verification.**
Catalog parsing, exact weights, namespace behavior, source URLs, and overwrite
rejection are covered by the 56-test Radeon suite. **Status: implemented and
verified at contract level; balanced episodes not yet collected.**

### Record 14: controlled ACT and Diffusion variables

**Evidence.** Several model choices were hard-coded, preventing matched
ablation. Runtime inspection of pinned LeRobot 0.6.1 confirmed the supported
fields and showed that ACT observation history is fixed to one step. **Decision.**
Expose supported variables only and guard temporal ensembling and Diffusion
horizon invariants. **Verification.** Bash syntax and CLI entry checks passed on
the Radeon host. **Status: implemented; most combinations still require runs.**

### Record 15: compact Diffusion smoke and one rejected integration attempt

The initial list argument was emitted as three CLI tokens and was rejected
before policy construction. After changing it to one list-valued token, the
`[256,512,1024]` model parsed correctly, used 76,597,288 parameters, completed
one AMP training step in 23.60 seconds of progress time, and saved a checkpoint.
The previous default smoke had 263,762,728 parameters and about 53 seconds
including setup. **Decision: keep the compact configuration as a candidate,
repeat with a meaningful budget, then rank only by matched closed-loop task,
safety, and latency results.**

## 2026-07-24: catalog v2 evidence-driven control revision

### Record 16: establish a stratified catalog v2 baseline

One deterministic 20-second episode was run for each of the twelve training
profiles on the single Radeon. Eight profiles completed: `micro_box`,
`small_carton`, `flat_mailer`, `book_box`, `long_carton`,
`upright_canister`, `near_limit_box`, and `electronics_box`. The medium carton
and shoe-box proxy hit the 35 N safety boundary, the large narrow carton
remained in approach, and the mailing tube rolled away during approach. This
is a twelve-case regression smoke, not an estimated success rate. **Decision:
keep the baseline as diagnostic evidence and require multi-episode evaluation
before any capability claim.**

### Record 17: reject two high-box grasp candidates

The height-aware candidate increased pregrasp height for tall parcels. It did
not add a successful profile. A second candidate descended after closing to
seat the grasp; it also added no success and produced peaks of 51.10 N, 51.64 N,
and 48.33 N on the three targeted boxes. Both candidates violated the task or
safety acceptance criteria. **Decision: reject both defaults and restore the
original expert.** The JSON traces remain under `evidence/catalog/` so the
negative result is reproducible.

### Record 18: separate mailing-tube physics from grasp control

The baseline tube moved roughly 4.2 m without finger contact, indicating a
physics problem before a policy problem. Genesis rolling friction was enabled;
the first attempt failed during scene construction because Genesis 1.2.3
requires torsional friction whenever rolling friction is enabled. Enabling both
solver options and setting tube rolling friction to 0.002 reduced short-horizon
drift to 18.3 mm, but the open gripper made a 79.27 N single-finger contact.

Three control candidates were then tested on the same episode. A 2.5 mm final
approach step still aborted at 36.74 N; 2.0 mm was worse at 98.83 N; a 5 mm XY
alignment tolerance avoided contact but chased the moving tube for the full
20 seconds. These profile-specific control overrides were removed. Increasing
rolling friction to 0.005 reduced short-horizon drift to 3.3 mm, but the grasp
still aborted at 73.99 N. **Decision: keep the physical rolling-resistance
support and 0.005 catalog candidate, reject the control overrides, and report
mailing-tube manipulation as unresolved.** A staging cradle or an end-effector
change is now preferred over further single-episode tuning.

### Record 19: current optimization order

1. Complete the full catalog regression after the solver change.
2. Collect at least 300 successful, balanced RGB-D expert episodes.
3. Train ACT with three seeds and rank checkpoints by held-out closed-loop task
   success, then safety and latency.
4. Train compact Diffusion under the same split and evaluation protocol.
5. Add depth through a separate encoder and matched RGB versus RGB-D ablation.
6. Audit VLA-Adapter 0.5B licenses and ROCm operators in isolation; integrate it
   for semantic bin selection only after both gates pass, keeping continuous
   control and safety below it.
7. Profile simulation, rendering, host-to-device transfer, and inference before
   applying ROCm-specific tuning.
8. Add ROS 2 only after the simulator-policy contract is stable.

This order optimizes the scored robot capability first while preserving a
credible ROCm, multimodal, robustness, and deployment story.

### Record 20: scope the Genesis rolling solver path

Enabling rolling and torsional friction globally caused the catalog smoke to
drop from 8/12 to 6/12: `micro_box` and `electronics_box` regressed. The
profile comparison showed the new failures were unrelated to rolling parcels.
The solver flags are now enabled only when the sample is a horizontal cylinder
with a positive rolling coefficient; ordinary boxes and upright cylinders use
the previous solver path. A 58-test Radeon suite passed, and the full scoped
catalog returned to the original 8/12 profile result. **Decision: keep the
scoped physical correction and the regression artifact; reject the global
solver setting.**

## 2026-07-25: centered mailing-tube grasp and scoped stabilization

### Record 21: repair cylinder sampling before control tuning

The horizontal-cylinder radius and initial height were derived from two
independently sampled dimensions. The fixed mailing-tube sample therefore
spawned about 5 mm above the table. Cylinder sampling now shares one radial
dimension, and spawn height uses the constructed radius. The gripper yaw was
also corrected so finger length follows the tube axis and closure crosses the
diameter. Axis alignment reduced the fixed diagnostic peak from 72.92 N to
43.54 N, but did not yet pass safety. **Decision: keep both geometry fixes;
they correct the modeled system rather than tune around an invalid state.**

### Record 22: phase-specific approach, verification, and lift control

Mailing-tube profiles now support a 5 mm final approach and 10 mm lift step.
Three consecutive bilateral-contact frames are required before lift. On the
fixed diagnostic, the 5 mm approach passed the contact gate at 34.26 N; stable
verification then exposed slip during lift. The 10 mm lift request extended
contact but still failed during recovery. **Decision: keep these as scoped
contact-phase variables, not as a success claim.**

### Record 23: retain friction pads and centered close pose

Setting tube-profile finger friction to 2.0 reduced the peak to 15.62 N and
allowed all three attempts to enter lift. Trace inspection then showed the
generic 35 mm cylinder tolerance closed about 33 mm above the intended pose.
A 10 mm profile tolerance produced the first true lift: tube center rose from
30.9 mm to 66.4 mm with about 75 frames of bilateral contact before slipping.
**Decision: retain both material and pose corrections; report the tube as an
unresolved partial capability.**

### Record 24: reject force escalation

Profile close-force candidates of 25 N and 35 N raised the maximum tube center
only to 69.2 mm and 69.9 mm. Measured peaks were 36.46 N and 35.19 N, both over
the frozen 35 N boundary, and neither completed lift. The optional close-force
field was removed from production code. **Decision: reject; marginal height is
not worth a safety regression or a larger configuration surface.**

### Record 25: scope stabilization after a full-catalog regression

The first full regression with global three-frame stability fell from 8/12 to
5/12; `flat_mailer`, `book_box`, and `near_limit_box` regressed. Stability is
now a profile override: global one frame, mailing tubes three. Sixty-seven
tests passed on Radeon, and the second full regression restored the exact 8/12
per-profile completion pattern. Both JSON files are retained. **Decision: keep
the scoped implementation and treat 8/12 only as a regression smoke.**

## 2026-07-25: metric depth repair and RGB-D policy path

### Record 26: find and classify the historical depth defect

The 96-episode dataset reported a depth median of 0.00117156 m. Upstream Genesis
camera code defines near/far planes in metres and reconstructs point clouds from
the returned depth without a 0.001 factor. The project conversion was therefore
wrong. The old encoded data is retained for RGB/state ACT reproducibility and
explicitly rejected for RGB-D; it is not silently rescaled.

### Record 27: implement and exercise the corrected path

New collection stores raw float32 metric depth and a deterministic 3-channel
0.25-4.0 m view. A metadata audit gates training, while checkpoint config drives
RGB or RGB-D inference. Seventy-one Radeon tests passed. A one-episode shard
contained 152 frames with 0.737-3.535 m depth and passed strict RGB-D audit.

The first one-step training command was rejected before model creation because
`eval_split=0` was paired with nonzero evaluation steps. A shell preflight now
rejects that combination. The corrected retry completed one ACT update with
51,577,736 parameters and two visual inputs, then saved and reloaded the model.
One Genesis closed-loop run completed with 3.48 ms mean and 11.53 ms P95 model
latency but did not solve the task. **Decision: keep as end-to-end interface
evidence; collect balanced data before comparing capability.**

### Record 28: gate the VLA route by license and Radeon compatibility

Model research found that OpenVLA inherits Llama 2 weight terms, openpi states
an NVIDIA GPU requirement, and the current SmolVLA checkpoint metadata does not
declare a license. VLA-Adapter 0.5B is smaller and has MIT-tagged public
components, but its official setup is CUDA-oriented and its transitive assets
still require review. **Decision: keep ACT and Diffusion as the reproducible
main line; treat VLA-Adapter as an isolated compatibility study only after both
license and ROCm gates pass. Do not present any VLA as a current capability.**

### Record 29: separate realistic parcel boundaries from trainable hardware scope

Five sourced boundary profiles were added to catalog v2: a USPS large flat-rate
box, a rigid proxy for a flat-rate envelope, large rectangular and square
cartons, and a large horizontal cylinder. Every profile has zero training weight
and is evaluation-only. The handling class records the missing hardware:
`suction_required` for the oversized/flat boxes and `cradle_required` for the
large cylinder. Tests protect these flags, URLs, and size boundaries.
**Decision: retain the catalog evidence, but do not claim suction or cradle
execution until those end effectors exist and pass fixed held-out trials.**

### Record 30: make small-sample task metrics honest

The result summary now includes numerators, denominators, and Wilson 95%
intervals for total success, first-attempt success, retry recovery, and drops.
When no episode retries, the recovery interval is `[0, 1]`: no recovery sample
exists, so a narrow zero interval would be false precision. The function rejects
invalid counts and non-positive/non-finite z scores. The local suite increased
from 71 to 73 tests and passed; Python compilation also passed. Git Bash syntax
validation and the complete test suite remain scheduled on the target Radeon
after synchronization. **Decision: retain; all future comparison reports should
show counts and uncertainty, not percentages alone.**

### Record 31: reconcile catalog counts before release

The current TOML contains 21 profiles: 12 training profiles and 9
evaluation-only profiles. Several release documents still described the older
four-boundary snapshot. The current README, technical report, dataset card, and
component matrix now say “nine,” while historical journal entries retain their
original snapshot context. **Decision: make every future catalog change update
the parser-backed count and current documentation in one commit.**

### Record 32: freeze the split before model comparison

LeRobot's default evaluation split is only reproducible when the input episode
list is fixed. The new splitter validates a completed collection, maps original
audit IDs to compact successful-episode indices, stratifies by profile, and
emits train, validation, and held-out lists. ACT and Diffusion consume the same
manifest through `DATASET_SPLIT_MANIFEST`; held-out episodes are excluded from
training. **Decision: keep the manifest as a required boundary for all matched
seeds and modalities.**

### Record 33: add a sequential model matrix

The new Radeon sweep entry fixes seeds 11, 22, and 33, runs one model cell at a
time, covers ACT RGB/RGB-D first, and can add compact Diffusion after the ACT
gate. Each cell writes a separate log and a CSV status row; failures remain
visible and do not change later conditions. **Decision: keep the sweep as the
only supported way to launch the matched model matrix.**

### Record 34: add a bilingual engineering playbook

The repository already contained a roadmap, decision log, and development
journal, but the learning path was spread across several documents. The new
`ENGINEERING_PLAYBOOK.md` and `ENGINEERING_PLAYBOOK_CN.md` consolidate the
workflow from requirement framing through contracts, tests, one-variable
experiments, safety/performance gates, and release evidence. **Decision: keep
the playbook as a navigation and method document, while leaving raw results in
the existing journals and evidence directories.** This avoids duplicating
claims and gives every future change a common record template.

Local verification completed with 76 unit tests, Python compilation, and
`git diff --check`. Radeon collection remains asynchronous; no remote model
result is claimed until its summary, split manifest, checkpoint, and held-out
closed-loop evaluation exist.

### Record 35: make checkpoint comparison matched and profile-balanced

The previous ranker prevented duplicate episodes within one checkpoint but did
not require different checkpoints to use the same episode set. It also ranked
only by aggregate success, allowing a frequent box profile to hide a failed
tube profile. The evaluator now rejects unmatched episode sets and inconsistent
force thresholds, reports Wilson intervals and per-profile results, and applies
a safety-first, macro-profile ranking. A canonical SHA-256 fingerprint also
proves that matching episode IDs contain identical randomized samples.
**Decision: keep this as the mandatory model-selection protocol.** Eighty-one
local tests and Python compilation pass;
no historical score is changed until its raw summaries are reprocessed.

### Record 36: make end-effector support executable and auditable

The catalog intentionally distinguishes `parallel_jaw`, `suction_required`,
and `cradle_required`. The scene currently contains only the first tool.
I added a pre-Genesis capability check and paired capability-contract
documentation. This is a small but important engineering step: unsupported
hardware must fail clearly instead of being treated as a successful robot
generalization result. Unit tests cover both the current path and a future
explicit registry extension. The remote dataset collection remains separate
from this local change and is not reclassified by it.

### Record 37: repair cross-platform sweep startup and retry isolation

The completed dataset triggered the sweep as designed, but the copied shell
entrypoint contained a UTF-8 BOM and the failed LeRobot cells then reserved
their output directories. I stopped only the watcher, preserved its logs, made
the shebang portable, and added an explicit output-root override for retries.
This separates infrastructure failure evidence from model evidence and keeps
the original failed cells available for diagnosis.

### Record 38: keep checkpoint-directory ownership with the trainer

The BOM fix exposed a second orchestration bug: creating a cell directory
before calling LeRobot made the trainer reject every fresh run under
`resume=false`. The sweep now creates only its root namespace and lets
LeRobot create each checkpoint directory. The next retry uses a new root, so
the two infrastructure failures remain available as negative evidence.

### Record 39: stage a bounded smoke matrix before long training

Once the corrected pipeline reached real training, its observed throughput
made a 30K x six-cell matrix a multi-hour commitment. I therefore chose a new
5K-step root for integration validation. This is deliberately not a model
selection result: it must produce loadable checkpoints first, then be evaluated
with the same held-out protocol before any scientific claim.

### Record 40: fix watcher override precedence

The first five-thousand-step request was parsed as thirty thousand because the
watcher overwrote the inherited environment before inspecting it. Replacing
that pattern with shell parameter defaults makes externally supplied budgets
effective. The next attempt will be accepted as a 5K smoke run only if the
trainer's resolved configuration says `cfg.steps=5000`.

### Record 41: freeze the completed collection as smoke-only evidence

The Radeon collection completed 400 audited episodes. Only 190 successful
episodes entered the LeRobot dataset, yielding a deterministic 123/24/43
train/validation/held-out split. The first ACT smoke cell confirms ROCm
preflight and `cfg.steps=5000`. **Decision: keep the matrix as an integration
smoke only.** The project still needs at least 300 balanced successful RGB-D
episodes before a 30K model comparison or closed-loop ranking can be treated as
formal evidence.

### Record 42: attribute expert failures before changing the controller

The trace-rich 400-attempt Radeon summary was processed without rewriting its
historical result. The analyzer reports 190/400 successes and 161/400 force
safety violations. The inferred last non-abort context is `approach` for 104
violations and `initial_state` for 22. `large_narrow_carton` is the first
diagnostic target: it completed 2/20 attempts and triggered 17 force aborts.

The implementation classifies force aborts, approach timeouts, grasp
verification failures, lift losses, drops, and placement failures. It also
reports Wilson intervals, phase reach counts, force distributions, profile
priority, and descriptive geometry/physics factors. **Decision: keep the
analyzer and start with safe reset/home geometry plus size-aware approach; do
not raise the 35 N limit.** Any controller candidate still requires a matched
fixed-episode A/B run and full-catalog regression before acceptance.

### Record 43: screen reset poses without promoting a CPU result

The new `--reset-qpos` diagnostic override makes the reset pose an explicit,
auditable variable while preserving the historical default. A CPU-only
kinematic screen on the same `large_narrow_carton` local episode rejected pose
A (`0,-0.785,0,-2.356,0,1.571,0.785`): it produced a 50.36 N abort where the
baseline completed. Pose C (`-1.0124,1.0,1.4,-1.6878,-1.5799,1.7757,1.4602`)
completed that episode with 10.86 N peak force versus the baseline's 32.24 N.

**Decision: hold pose C for a single-GPU Radeon A/B run; do not change the
default from CPU evidence.** CPU screening only ranks candidates and is not a
competition result because the task requires AMD Radeon execution. The exact
Radeon command is documented in the README and the candidate remains subject
to matched episode, full-catalog, and throughput gates.

### Record 44: close the final runtime-configuration validation gap

`--reset-qpos` previously replaced configuration after TOML validation, which
could let `NaN/Inf` bypass the finite-value contract. The entry point now
revalidates the complete configuration after every override. A new test injects
nine `NaN` values through the real CLI path and confirms exit before Genesis
environment construction. All 88 tests pass on Radeon. Reproduction commands
must explicitly select the current checkout's `src`, because the shared virtual
environment retains an editable install pointing to an older workspace.

### Record 45: promote the Radeon reset A/B from commands to a frozen protocol

The new one-command runner fixes 20 `large_narrow_carton` episodes, pose C,
single-device ROCm preflight, and matched-sample comparison. It refuses an
existing output root and generates a SHA-256 manifest for both summaries and
the comparison. The script passes Radeon shell syntax validation but has not
run yet; it waits for ACT smoke to release the only GPU.

### Record 46: complete and audit the ACT 5K smoke matrix

All RGB/RGB-D combinations for seeds 11, 22, and 33 completed 5,000 ACT steps
and wrote loadable checkpoints. The new evidence builder verifies the saved
configuration and hashes every checkpoint file, log, status table, and dataset
split. The resulting JSON remains explicitly smoke-only; it does not rank
models or clear the balanced-data gate.

### Record 47: reject pose C on Radeon evidence

The matched 20-episode run produced 1/20 baseline successes and 4/20 candidate
successes. Force aborts decreased from 12 to 9, but pose C still failed the 90%
success and 5% force-abort gates and regressed episode `7000005`. The default
pose therefore remains unchanged. The next isolated controller experiment is
size-aware approach clearance, not immediate data collection.

### Record 48: preserve complete artifacts across a Genesis cleanup crash

Pose C emitted a complete summary and normal Genesis exit message before a
status-139 cleanup crash. The runner now continues only for that exact status
when a strict summary postcondition passes. The comparison also enforces that
`control.reset_qpos` is the sole config difference. All 91 tests pass on the
Radeon environment.

### Record 49: reject the first size-aware transit candidate

The candidate added the parcel's vertical-envelope delta and a 20 mm margin to
horizontal transit clearance. On the fixed Radeon 20-episode match it produced
0/20 successes, 12 force aborts, and a 304.67 N peak, while regressing baseline
episode `7000005`. Trace attribution showed the regression after a lost-grasp
retry, so the candidate remains disabled and the complete negative-control
artifacts are stored under `evidence/expert/radeon-size-aware-ab-v1-*`.

### Record 50: test recovery-aware retry separation

The next isolated change added a 120 mm lateral retreat only after
`retry_count` increased. The first-attempt path and safety threshold were
unchanged. The matched Radeon result improved from 1/20 to 2/20, recovered one
episode with no regressions or drops, and reduced force aborts from 12 to 11,
but still failed the absolute task and safety gates. Keep the feature disabled
by default; retain it as a candidate for a larger pre-registered recovery study.

### Record 51: make detached Radeon experiments self-contained

The first size-aware run lost its shell continuation after the SSH stdout pipe
closed, even though the baseline summary was complete. Both A/B runners now
redirect each expert leg to a versioned log inside the output root and hash the
logs with the summaries and comparison. This is an operational reproducibility
fix, not a task-performance claim.
