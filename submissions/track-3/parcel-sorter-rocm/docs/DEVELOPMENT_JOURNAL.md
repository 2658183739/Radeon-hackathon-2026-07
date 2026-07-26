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

### Record 52: reject a smaller free-space approach step and preserve compact evidence

The failure analyzer showed that the diagnostic carton profile is dominated by
approach timeouts and force safety aborts. I tested one hypothesis in isolation:
reduce `control.approach_step_m` from 0.040 m to 0.020 m on the same 20 Radeon
episodes. The candidate reached 0/20 successes versus 1/20 for the baseline,
kept 12/20 force aborts, and raised peak force from 111.28 N to 161.28 N. It
was rejected and the historical 40 mm default remains active.

The full summaries contain 600 trace frames per episode, so I added
`scripts/compact_expert_summary.py`. It preserves the source digest and size,
runtime, complete configuration, episode randomization, terminal results, and
profile summaries while explicitly marking `trace_omitted`. The remote full
summaries and their remote hash manifest remain the provenance record; Git
stores the compact summaries, failure analyses, logs, comparison, and a local
hash manifest. This keeps review artifacts small without presenting a compact
file as if it contained raw traces.

Validation: 101 Radeon unit tests, shell syntax validation, the two failure
analyses, and the machine comparison completed. The next experiment must target
the approach/retry state machine rather than tuning this step in isolation.

### Entry 53: Contact-brake A/B exposes an observation-timing limit

Implemented a disabled-by-default approach contact brake with a 20 N trigger
and at most 10 mm separation, including config, CLI, expert-action, and runner
regression tests. The fixed 20-episode Radeon A/B produced the same 1/20
successes, 12/20 force aborts, and zero drops, while candidate peak force rose
to 467.31 N. Trace evidence shows the critical episode jumped from 0 N on the
previous frame directly to 467.31 N on the abort frame, so observe-contact-now,
brake-next-frame is too late in the current 30 Hz loop. Keep the candidate off
and prioritize a pre-contact geometric guard or high-rate compliant control.
Post-processing initially rejected an overdeclared config-difference whitelist;
after correcting it, the complete summaries were reused without rerunning the
GPU experiment.

Validation: 104 unit tests in the Radeon environment, runner shell syntax,
Python compilation, both failure analyses, and local evidence hashes passed.

### Entry 54: The vertical-barrier candidate changed impulses but broke success

Added disabled-by-default `approach_barrier_recovery_step_m`: when the end
effector is below the transit height but still away from the parcel, freeze
horizontal motion and allow a 120 mm vertical recovery step. The fixed Radeon
A/B produced 0/20 successes and 12/20 force aborts for the candidate versus
1/20 and 12/20 for baseline. Episode `7000007` improved to 32.99 N peak force,
but baseline success `7000005` regressed to a 42.43 N force abort. The barrier
therefore needs geometric clearance and low-level tracking constraints together;
enlarging one step is not sufficient. The candidate stays disabled, with full
summaries, failure analyses, logs, and SHA-256 archived. Radeon validation now
passes 107 tests.

### Entry 55: AABB API validation, guarded implementation, and rejection

I first verified the real Genesis 1.2.3 API on the Radeon host instead of
assuming its return type. `left_finger.get_AABB()`, `right_finger.get_AABB()`,
and `parcel.get_AABB()` each returned a `(2, 3)` `torch.Tensor` on ROCm device
`cuda:0`. This allowed axis-gap calculation to stay on the GPU, with one scalar
synchronization for the audit value.

The implementation kept the candidate disabled unless a positive distance was
provided by CLI/config. It filtered only a pre-descent approach that was moving
horizontally toward the parcel, kept the 8-D policy action schema unchanged,
and wrote a separate safety trace containing AABB gap, nominal and filtered
targets, trigger reason, cumulative count, active duration, and measured cost.
The matched runner froze one Radeon, one profile, 20 episode IDs, one allowed
config difference, postconditions, failure analyses, logs, and hashes.

A 20 mm smoke never triggered because the smallest pre-descent gap was about
30.2 mm. The 40 mm smoke triggered six times, so 40 mm became the single
pre-registered candidate rather than an arbitrary sweep. The formal A/B then
triggered 65 times but reduced success from 1/20 to 0/20, retained 12/20 force
aborts, added one approach timeout, and regressed `7000005`. It was rejected.
The comparison now aggregates guard activity and compute cost, and compact
summaries preserve safety telemetry while omitting frame traces.

Validation: 121 local tests, 116 Radeon tests, shell syntax, fixed comparison,
failure attribution, and local/remote SHA-256 verification. The lesson is that
a conservative implementation and a functioning trigger do not imply an
effective safety controller; AABB is too coarse to replace signed distance,
contact-aware low-level control, or a correct recovery state machine.

### Entry 56: Lower approach gains trade force aborts for tracking timeouts

I implemented command-scoped arm-gain scaling instead of changing the policy
interface. Kp is multiplied by a configured scale, Kv by its square root, and
finger gains remain fixed. The environment changes gains only for the delayed
action actually executed as `MOVE_PREGRASP`; all other commands restore the
nominal gains. A default of 1.0 therefore reproduces the historical controller.

The probe sequence was deliberately bounded. Scale 0.25 timed out with zero
contact, proving that excessive compliance lost tracking authority. Scale 0.50
kept successful episode `7000005`, while a second probe still timed out, so it
was promoted to one fixed A/B rather than a parameter sweep. On the complete
Radeon match, force aborts improved from 12 to 10 but timeouts worsened from 7
to 9; success stayed 1/20, peak force stayed 111.28 N, and throughput retention
was only 0.751. The candidate is rejected and the default remains 1.0.

The learning point is that a lower joint-space stiffness is not equivalent to
a contact-aware Cartesian impedance controller. It can reduce some measured
forces while slowing convergence and moving failures between categories. The
next design must constrain Cartesian approach velocity/energy near contact and
define recovery explicitly. Validation included 123 Radeon tests plus 6
subtests, the exact single-config comparison, failure attribution, compact/full
hash manifests, and retained run logs.

### Entry 57: Prove the velocity API, then reject the task controller

I checked the installed Genesis source before coding: Jacobian translation is
stored in rows 0--2 and rotation in rows 3--5. The first equal-weight DLS smoke
spent too much authority on orientation, so I introduced an explicit 0.20
orientation weight rather than changing unrelated state-machine tolerances.
An isolated Radeon check then proved the full API path: the robot accepted a
velocity command, measured joint speed reached about 1.03 rad/s, and the end
effector descended about 25 mm.

The integrated smoke taught a different lesson. The solver predicted about
-0.078 m/s vertical motion, while measured joints stalled near 0.005 rad/s
beside the large carton. That points to physical blocking by the hand/carton
geometry, not a reversed Jacobian or failed ROCm operation. I therefore kept
the implementation observable: it logs requested and predicted twists,
commanded and measured joint velocities, pose error, sample count, and
synchronized computation time.

The fixed 20+20 A/B rejected the candidate: success changed from 1 to 0,
force aborts from 12 to 13, and throughput from 17.80/hour to zero. Although
P95 force improved, maximum force did not, and `7000005` regressed. The
default remains off. Validation is 128 formal Radeon tests plus 6 subtests,
shell syntax, comparison, two failure analyses, logs, and local/remote hashes.
The next code should express feasible hand/carton geometry and recovery
states before tuning another continuous controller.

### Entry 58: Diagnose initialization collision before changing control again

I added a deferred-settle diagnostic path so the scene could be inspected at
every 240 Hz physics substep before the ordinary initialization settle. The
script records bidirectional geometry/link mappings, contact forces, poses, and
the exact first-contact substep. This showed that `7000001` did not first fail
during approach: its hand already intersected the carton at substep zero and
generated about 1.27 kN. The successful control `7000005` started collision
free. That evidence changed the next experiment from another controller tune
to a reset-feasibility check.

The implementation queries Genesis `detect_collision()` before integration,
filters unordered pairs to robot/parcel geometry ranges, and selects a fixed
fallback qpos only on collision. A second query is a mandatory postcondition;
remaining collision raises an error instead of silently starting the episode.
The feature remains off by default, and the comparison reports checked
episodes, fallback count, initial/fallback pair counts, and compute time.

The fixed 20+20 Radeon result improved four failed episodes and regressed none,
but reached only 5/20 successes with 8/20 force aborts. This is a useful root-
cause intervention, not a release candidate. I retained the code and evidence
for reproducibility while keeping the default disabled. Validation is 134
Radeon tests plus 6 subtests, the two substep diagnostics, exact-config A/B,
failure analyses, logs, compact summaries, and local/remote hashes.

### Entry 59: Use sequential probes to reject a tempting tolerance fix

Trajectory inspection showed a clean pattern: all seven high-carton timeouts
were nearly centred in XY and stalled 40--50 mm above the nominal hand pose.
Instead of immediately running 40 episodes, I implemented an opt-in geometric
capture predicate and ordered three probes so the cheapest falsification came
first. The predicate split horizontal and vertical feasibility and derived the
upper band from carton height, a minimum side overlap, and a hard cap.

The first version demonstrated how sensitive a hybrid controller is to event
timing. Expanding the low-carton window by only about 2 mm moved closure by one
control frame and turned a known success into a force abort. I then isolated the
rule to the already identified high-carton stratum. That preserved the known
success but changed the target timeout into a more dangerous grasp/retry abort.
The predeclared stopping rule ended the experiment before the third probe.

The code remains disabled because a negative experiment is still useful for
teaching and reproducibility. The important lesson is that a state predicate
cannot repair kinematic infeasibility: the pose generator, collision check, and
recovery transition must agree on the same physically stable grasp. Validation
covered 140 Radeon tests plus 6 subtests and verified compact/full provenance
hashes for every executed probe.

### Entry 60: Generate feasible poses, reject an expensive guard, and reach 75%

The next branch implemented the missing geometric capability instead of
loosening another state predicate. It generates 24 box-relative grasp poses,
solves each from up to three deduplicated joint seeds on Radeon, rejects IK/FK,
state-restoration, and non-finger collision failures, and ranks the remaining
poses by centred side contact, joint travel, manipulability, and clearance.
The selected full pose is shared across approach, capture, closure, and lift;
retry clears delayed actions and replans.

Sequential probes first protected known successes. A 125 mm scope boundary,
derived from 105 mm palm clearance plus 20 mm minimum overlap, kept episodes
`7000004`, `7000007`, and `7000010` on the historical path; all three remained
successful with zero planning attempts. Four high-box recoveries then remained
successful. A swept joint-segment collision gate was falsified next: six force
challenges produced zero waypoint rejections, still all force-aborted, and paid
1.66--7.76 seconds of synchronized checking per episode. The gate was changed
from default-on to an explicit diagnostic switch.

The force failures did respond to pre-contact step size, but non-monotonically.
A scoped 5 mm approach recovered four of six challenges while two remained
unsafe. A global 2.5 mm approach fixed those two but regressed two medium-height
boxes. The final policy therefore uses a geometry-derived split: 5 mm below
160 mm and 2.5 mm at or above 160 mm, where 160 mm is the 105 mm palm envelope
plus the 55 mm maximum vertical candidate offset. Four cross-sentinels all
selected the intended step and succeeded before formal A/B began.

The fixed single-Radeon 20+20 comparison improved success from 5/20 to 15/20,
recovered ten failures with no regression, reduced force aborts from 8/20 to
4/20, retained zero drops, reduced maximum force from 111.30 N to 46.99 N, and
raised successful throughput from 98.25/hour to 359.36/hour. It still missed
the 18/20 success and at-most-1/20 force-abort gates, so the planner remains
disabled by default and model/data work stays gated. Validation passed 162
Radeon tests; compact/full artifacts, logs, failure analyses, and hashes are
archived under `evidence/expert/radeon-geometry-aware-grasp-planning-*`.

### Record 61: Build the matched multi-profile evidence layer

The repository and Radeon instance were audited before launching more physics.
The GPU was idle with 47.98 GiB VRAM and 71 GiB workspace free. The existing
campaign validator already fixed ROCm, one GPU, and the 35 N boundary, while
the expert runner already exposed four planner ablations. Missing pieces were a
three-group scheduler, exact paired inference, profile-stratified continuous
effects, and a switch for removing the tiered approach policy.

The implementation adds dependency-free exact McNemar, deterministic paired
bootstrap and sign-flip tests, Wilson intervals, force/duration/latency
distributions, planner timing, and profile macro results. A frozen 12-profile
screen uses five new local episode IDs per profile across historical, reset,
and geometry groups. A second namespace is reserved rather than inspected.

Focused Radeon validation passed four new statistics tests and seven campaign
tests, Python compilation, shell syntax, and campaign fingerprint validation.
The analyzer also replayed the existing 20+20 geometry artifacts and recovered
the expected 5/20 and 15/20 summaries. This validates evidence plumbing only;
the 12-profile campaign result remains unknown until execution finishes.

### Record 62: Reject universal planning after the balanced Radeon screen

The frozen campaign completed 180 closed-loop episodes on one Radeon GPU: 12
parallel-jaw profiles, five matched episodes per profile, and historical,
collision-checked-reset, and complete-planner groups. Historical control
reached 36/60 successes and 16/60 force aborts. Collision-checked reset reached
38/60 and 15/60. Complete geometry planning also reached 38/60 and 15/60, with
zero drops in every group.

Relative to reset alone, complete planning changed mean episode peak force by
+1.65 N (paired bootstrap 95% CI -1.67 to +5.99 N). Exact McNemar tests for
both success and force abort returned p=1.0. Each planning attempt cost 5.57 s
on average. Profile inspection showed one recovery in `large_narrow_carton`,
one apparent recovery in `shoe_box_proxy`, and two regressions in
`medium_carton`; the aggregate method therefore failed the frozen advancement
gate and must not become the default controller.

Full trace replay exposed an important execution limitation. Two changed
episodes never activated the planner, yet their floating-point state diverged
before their control actions diverged. Genesis/GPU closed-loop execution is
therefore not bitwise deterministic under these runs. Discordant pairs cannot
all be attributed to the method without execution repeats. The evidence is
archived under `evidence/expert/radeon-geometry-screen-v1`, while local episode
IDs `200000`--`200039` remain untouched for later confirmation.

The next development-only hypothesis uses an existing causal risk signal rather
than another fitted size threshold: permit planning only when collision-checked
reset detected an initial robot/parcel intersection and actually selected the
collision-free fallback pose. This would have excluded the observed
`medium_carton` planning regression while retaining the genuinely activated
`large_narrow_carton` recovery. It must still pass new probes and an independent
validation namespace before any performance claim.

### Record 63: Integrate and probe the reset-fallback risk gate

The implementation adds a default-off task flag, validates that it cannot be
used without both collision-checked reset and geometry planning, and resolves
planner activation only after the reset collision query. Environment telemetry
now distinguishes static eligibility, gate satisfaction, final activation, and
avoided planning. The runner reads actual environment activation before choosing
the stable-contact dwell, so skipped planning preserves baseline timing.

A matched comparison aggregate was added for eligible, gate-satisfied, active,
and avoided episodes plus planning attempts and compute time. The method has a
three-case mechanism runner and a separately frozen 12-profile validation
campaign using new local IDs `120000`--`120004`. Local and Radeon validation
passed 183 and 178 tests respectively; the campaign fingerprint is
`046fb98cf08c900df36799c5ffc3d2863a67f1a9a62adc0c7602e9e84af98507`.

Three single-Radeon probes then passed their mechanism contracts. Non-risk
`4100004` skipped planning and succeeded at 6.05 N. Risk episode `7100002`
used fallback reset, planned once, and succeeded at 9.23 N. Low-box sentinel
`1100000` skipped planning and succeeded at 7.18 N. These outcomes permit the
new validation campaign to run but do not establish an effect size.

### Record 64: Reject the gate and isolate execution-order effects

The frozen 60+60 development validation completed on one Radeon GPU. Reset
baseline produced 35/60 successes, 17/60 force aborts, and zero drops; the
gated candidate produced 33/60, 19/60, and zero drops. Mean episode peak force
changed by +6.67 N with a paired bootstrap 95% interval of -0.53 to +16.85 N.
Five planner-active episodes contained one recovery and two regressions. The
new gate avoided zero planning episodes beyond static geometry eligibility,
so both its safety and work-saving hypotheses failed.

Before reading the complete result, a causal-attribution audit was added and
tested. It partitions planner-active from planner-inactive episodes, validates
gate telemetry, and compares trace state and high-level decision divergence.
It identified `5120000` as inactive-planner drift: state changed at frame 104
and the decision at frame 121. The validation and all derived artifacts were
hashed and archived before selecting the follow-up.

The follow-up froze four discordant episodes, five repeats per condition, and
a seeded blocked order with 10 baseline-first and 10 candidate-first blocks.
An initial process-per-observation executor was stopped before result review
because every process recompiled Genesis kernels for about 80 seconds. Its
incomplete output was isolated remotely. A replacement kept the exact schedule
but executed new scenes in one process, cutting repeat runtime without changing
samples, controls, or the 35 N boundary. The code explicitly labels 40 runs as
nested measurements of four experimental units.

All three planner-active changes repeated exactly five times: two regressions
and one recovery. The inactive `5120000` succeeded 2/5 under both conditions;
all four successes occurred when the condition was second in its block. This
is a process-local period/carry-over signal, not an inactive-planner effect.
The method remains rejected. Radeon validation passed 182 tests, Python
compilation, shell syntax, and local/remote SHA-256 verification.

### Record 65: Use phase telemetry to reject universal transport limiting

The three planner-active episodes shared the same grasp family but produced one
recovery and two regressions. The first transport contract reduced `4120001`
from 159.27 N to 12.82 N but timed out because dwell counters repeatedly reset.
A 20 mm step restored the 158.81 N impact. Monotonic raise and transfer latches
then retained the `5120003` success and recovered `7120004` from 69.00 N to a
13.88 N success.

`4120001` exposed the remaining speed-versus-retention conflict: a 10 mm target
derived from measured pose required 301 transport frames and slipped, while
bounded lookahead produced 39.95 N and 40.95 N at 10 mm and 5 mm increments.
The 35 N gate stopped expansion. Code, CLI, 186 passing tests, compact evidence,
and full-summary hashes are archived. The next record must address payload-aware
grasp stability rather than another transport-step scan.

### Record 66: Reject infeasible deeper grasp families before integration

The grasp-stability investigation first separated static feasibility from
loaded transport behavior. The original top-down family produced 36 feasible
IK/collision evaluations out of 72. Three long-axis side-grasp clearances each
produced zero feasible candidates out of 24, while all 24 oblique 30/45-degree
candidates solved IK but collided with the stock Panda hand.

These candidates remain diagnostic-only. Connecting them to the controller or
silently extending the stock fingers would overstate the implemented robot.
The source generator records approach direction and palm-clearance metadata,
the compact Radeon evidence binds the full candidate artifact, and all 191
tests passed before the next mechanism was selected.

Frozen trace replay then identified a state-based slip signal. An 8 mm
single-frame relative jump, 6 mm downward component, 1 N contact floor, and
80 mm destination exclusion selected only frame 159 of `4120001`; it produced
zero triggers on the two successful sentinels. This froze a force-response
probe without claiming in advance that force could recover the grasp.

### Record 67: Reject force-only slip recovery after one gated probe

The implementation adds default-off slip telemetry and a 2 N, 15-frame close
force boost. A separate default-preserving lookahead switch reconstructs the
measured-pose feedback controller used to freeze the signal. Configuration
validation keeps the 22 N command target at least 10 N below the unchanged
35 N abort line, while telemetry records events, active frames, force target,
and maximum relative displacement. The full Radeon suite passed 200 tests.

On `4120001`, the detector fired at the frozen frame 159 and again at frame
261. Peak measured force remained below the gate at 22.92 N. The first boost
temporarily restored bilateral contact, but the carton continued descending;
final contact loss moved only from frame 260 to frame 261. Both baseline and
candidate failed after one retry in 19.97 s.

The primary mechanism probe failed, so the two successful sentinels and all
threshold/force scans were cancelled. The code is retained as a disabled,
auditable negative control. Reconsideration requires a capture-geometry or
recovery-state change, not a larger close-force command.

### Record 68: Isolate dynamic grasp candidates with complete scene snapshots

The next diagnostic asked whether a short loaded rollout could distinguish the
known unstable `4120001` grasp before full transport. Each candidate started
from the same complete Genesis `SimState`, not from a partial robot/parcel
reset. Restore checks covered robot and parcel positions and velocities; the
maximum observed state-vector error was exactly `0.0`. Six unique statically
feasible candidates per episode were each repeated twice, and every repeated
metric was identical.

The frozen rollout used 24 close steps, a 30 mm lift, and a 30 mm transfer.
It labeled 8/12 `medium_carton`, 4/12 `shoe_box_proxy`, and 12/12
`large_narrow_carton` executions stable. However, the production `+40 mm`
grasp that is known to fail later in `4120001` passed both short rollouts. The
`+45 mm` candidate led it by only 0.00849 mm in maximum one-frame relative
motion. The snapshot method is reproducible, but the short horizon lacks the
predictive validity required for controller ranking. It remains a standalone
diagnostic.

### Record 69: Change recovery state, then reject adjacent-pose regrasp

The first response that changed physical state replaced force boosting with a
default-off `recover_setdown -> recover_release -> retry` path. On the frozen
slip event at frame 159, the arm kept the gripper closed, descended vertically
by at most 10 mm per control frame, and released at the original grasp-height
envelope or after 20 frames. Set-down completed at frames 160--179 with a
21.81 N peak; release completed at frames 180--183. This verifies that the
parcel can be returned safely before retry, but not that the task is recovered.

Without a blacklist, retry selected the same `+40 mm` candidate and aborted in
the second transfer at frame 322 with 129.45 N. A separate default-off option
blacklisted that candidate, proved it was excluded, and selected `+45.1 mm`;
the second transfer still aborted at frame 300 with 129.98 N. The set-down
mechanism worked and the ranking feedback worked, but neither passed the task
or safety gate. Both remain disabled negative controls. The stop rule cancelled
sentinels, scans, and new episodes; the next hypothesis must change loaded
support geometry or use a genuinely longer-horizon stability objective.

### Record 70: Separate idealized horizon coverage from production dynamics

The dynamic runner was first extended through the complete pre-release path:
raise, transfer, and descent used bounded Cartesian segments, fresh IK at each
waypoint, the 35 N gate, and phase metrics. All six `4120001` candidates passed.
Because that set included the `+40 mm` candidate already known to fail in the
production loop, increased path length did not repair predictive validity.
Direct waypoint execution had removed the approach residual, action-delay
queue, and feedback behavior that produce the real failure.

The next runner used a fresh scene per rollout and the normal expert,
supervisor, delay queue, transport phases, force abort, and terminal task
check. A diagnostic allowlist was applied before execution, with retries set
to zero; no controller or physics parameter changed. The forced `+40 mm`
candidate reproduced the missed destination, while centered `+45 mm` completed
at 10.31 N. Four alternatives succeeded and one crossed 35 N. Two repeated
`+45 mm` runs matched exactly. Two prior-success sentinels safely retained
their own statically feasible `+40 mm` fallback.

The result changes the next engineering unit, not the production ranker. The
counterfactual runner is accepted as a label collector; a hand-written height
preference is rejected as post-hoc fitting. New episode IDs must be frozen
before collecting a candidate-ranking dataset and training a lightweight
PyTorch/ROCm scorer. The scorer must beat the static rank on an untouched
paired holdout before any integration.

The final synchronized Radeon tree compiled cleanly and passed all 227 unit
tests with `PYTHONPATH` bound to that tree rather than the older editable install.

### Record 71: Build the ROCm scorer pipeline without enabling it

The next unit converted formal counterfactual JSON into a strict versioned
dataset. The builder rejects non-fresh scenes, requested/selected mismatch,
inconsistent force-abort labels, unknown categorical values, non-finite
features, duplicate rollout keys, and episodes absent from the frozen split
protocol. Twenty-eight structured features and four targets are explicit.

The first checkpoint is a two-hidden-layer 6,276-parameter MLP. Training,
checkpoint loading, prediction ranking, independent evaluation, cold latency,
and warm P50/P95 are now separate executable paths. An initial function-boundary
mistake made the shared rank key return `None`; the new evaluator test caught it
before full regression, and the corrected six-test unit passed.

The only physical labels used were the already observed six-candidate
`4120001` smoke group. A 1,000-step Radeon fit took 1.715 s and reconstructed a
safe successful choice, but training and evaluation rows are identical. The
result validates plumbing, checkpoint portability, and sub-millisecond warm
batch inference only. The model remains disconnected while 12 train, six
development, and six holdout episode IDs remain unobserved.

### Record 72: Stop after the frozen development diagnostic

Collection first exposed two execution-contract gaps. An episode where the
reset-fallback gate was inactive used to stop the whole batch, despite being
outside the scorer's decision scope. The runner now emits a structured skip
with no labels, and the dataset layer rejects that file as training data. A
complete six-candidate output could also be followed by the known Genesis
interpreter-cleanup segmentation fault. The collector now accepts only
`SIGSEGV/139` after strict identity, controller-contract, repeat-count, and
rollout-count postconditions; truncated output remains an error.

The manifest is now the dataset boundary. It selects only complete/reused
labels, ignores explicit inactive-gate skips, verifies source hashes, and
rejects partial campaigns. The evaluator also separates full-split metrics
from a named real-group latency batch, so the 5 ms gate measures exactly six
candidates instead of an arbitrary dataset size. New tests cover each failure
path before the Radeon campaign resumes.

The frozen train campaign processed all 12 episodes. Four were applicable and
produced 24 labels; eight were structurally skipped. Train labels contain three
successes and 14 safety aborts, with no `shoe_box_proxy` group. A fixed seed-42,
2,000-step fit took 2.502 s. Training reconstruction kept one success and
changed selected aborts from static 3/4 to model 0/4, but this remains in-sample.

Only one of six development episodes was applicable. Every one of its six
candidate rollouts aborted above 35 N and none succeeded. The model and static
rank therefore both produced an aborted failure; the model did not select the
minimum observed force candidate. Six-candidate steady P95 was 0.921 ms, but a
latency pass cannot establish utility. The scorer remains disconnected,
holdout remains locked and unobserved, and no parameter scan follows this
single-group diagnostic. The final Radeon tree compiled and passed 247 tests.

### Record 73: Measure contact wrench, then reject it as a selector

Genesis 1.2.3 source inspection and a live Radeon probe established the actual
contact contract: position, normal, penetration, both geom/link IDs, and forces
on both bodies are tensors on `cuda:0`. A pure reference metric now standardizes
force direction, computes bilateral friction-cone margins, force symmetry,
center-of-mass moment arms, gravity residual, and bounded disturbance reserve.
The environment records it only when an explicit telemetry flag is set; the
controller, candidate rank, and 35 N gate are unchanged.

Predictive summaries use fixed 0.1 s windows at the 30 Hz control rate. In the
observed `4120001` pair, the successful `+45 mm` candidate had larger early
friction and disturbance margins than failed `+40 mm`, but both early-loaded
windows remained robust. The frozen train group `7130001` then supplied the
stop evidence: its three successes and three failures overlapped, including a
successful pre-lift false negative and a later 100.70 N false positive. The
metric remains useful telemetry but is rejected as a selector; holdout remains
unopened.

A vectorized ROCm implementation matched the reference but increased the
matched 240 Hz run from 93.98 to 101.65 s because approximately eight contacts
per sample are too small for repeated GPU launch and synchronization. Sampling
only the last physics substep preserved metric direction, reduced raw output
from 14.3 to 6.0 MB, and reduced the matched run to 86.66 s. The final default
uses the faster CPU diagnostic scorer while Genesis physics/contact solving
remain on Radeon. All 254 tests pass on the synchronized ROCm tree.

### Record 74: Change loaded support geometry and stop after positive development evidence

The contact-wrench stop decision pointed to support geometry rather than
another threshold. A structured generator now derives a Panda MJCF from the
locked Genesis 1.2.3 asset and adds a 30 mm collision/visual extension to each
finger. The source meshes remain upstream. Configuration bounds the extension,
both production and counterfactual CLIs expose it explicitly, and telemetry
records the generated asset path and source contract. The switch is default
off and the 35 N supervisor is unchanged.

The first live probe failed only because `RigidGeom` has no public `name`
attribute. The reproducible probe was corrected to use link geom counts and
`ElementTree.iter("geom")`. It then built both Radeon scenes successfully:
each link gained one physical collision geom, the XML contained the expected
four collision/visual elements, and the world AABB extended by approximately
29 mm. The distinction matters because `RigidLink.geoms` excludes the
`contype=0` visual geometry.

The observed `4120001 +40 mm` mechanism run changed from a missed bin at
21.81 N to completion at 24.07 N. The known-success `+45 mm` sentinel remained
successful at 12.55 N. A frozen six-candidate `7130001` train comparison then
changed completion from 3/6 to 5/6 and safety aborts from 2/6 to 1/6. The only
remaining failure crossed 35 N and aborted at 36.95 N; successful adapter runs
peaked at 32.69 N or less. No holdout ID was opened.

The positive result triggers a stop, not a length scan. Thirty millimetres is
frozen and the capability remains default off. Eight paired executions from
two deterministic episodes are mechanism evidence rather than independent
samples. Documentation also records that the current generated geometry keeps
stock explicit finger inertials; real adapter mass, fasteners, compliance,
CAD clearance, and force calibration remain future requirements.

### Record 75: Add physical inertia, reproduce a sentinel regression, and stop

The next unit implemented the previously stated fidelity requirement instead
of starting a larger campaign. A uniform 30 mm adapter box at a fixed effective
density of 1240 kg/m3 adds 5.952 g to each 15 g finger. A pure helper combines
the stock and box centers and inertia tensors with the parallel-axis theorem;
the generated MJCF replaces `diaginertia` with `fullinertia`. Filenames,
configuration validation, three CLIs, geometry-probe output, and environment
telemetry now expose extension, density, mass, and inertia model explicitly.

Unit tests check mass, center, finite tensor values, and positive-definite
principal minors. Targeted remote tests passed before the live probe. Genesis
1.2.3 then accepted the tensor on Radeon/ROCm, retained the 6-to-7 collision
geom change and 56-to-85 mm AABB extension, and produced a generated-asset
SHA-256 of `c1785752199e90c2631c3bff46eb6733545d35f707819686dec590c236e95e32`.

The elimination gate reused only the observed `4120001` mechanism pair. The
known failed `+40 mm` grasp still completed, now at 13.14 N. The known-success
`+45 mm` sentinel then jumped from 5.06 N at frame 202 to an abnormal
19-contact, unilateral branch at frame 203 and aborted at frame 204 with
38.3364 N. One exact same-parameter repeat reproduced the complete outcome.

The stop rule cancelled `7130001` and all new episodes. No density, length,
controller, or safety-threshold tuning followed the failure. The code remains
useful as a default-off physical-model capability, but the mass-aware candidate
failed promotion. The next admissible diagnostic must independently specify
which contact-pair and finger-actuator signals to inspect around frames
202--204; it may not optimize against the observed sentinel.

### Record 76: Instrument the contact branch, catch a no-op experiment, and stop

A preregistered differential diagnostic captured all robot contacts and both
finger actuator states on every 240 Hz physics step over frames 196--204. The
stock-inertia geometry ablation completed at 12.55 N; the mass-aware condition
reproduced the frame-204 38.3364 N abort. Their first contact identity/count
difference occurred at 197/2, force separated at 197/4, finger position did
not exceed 0.1 mm difference until 202/0, and actual force/velocity exploded at
203/4 while the controller command remained identical.

The mass-aware peak was a 162.19 N stock-fingertip contact with 115.5 mm
reported penetration. The adapter collision appeared only after instability.
This orders the mechanism below high-level control and invalidates VLA or
visual-model tuning as a response to the failure.

The first 0.010 s equality-constraint command modified a generated asset, but
the environment regenerates that file from Genesis source at construction.
Review of the generation path caught the overwrite. That run is recorded as
an excluded no-op setup check, not interpreted as evidence. The corrected
command changed the source within a restoration trap, verified both source and
generated values, and removed the prior time-constant warning. It aborted even
earlier at frame 134 during raise with 105.85 N, before the frozen telemetry
window.

The candidate is rejected and adjacent time constants are not scanned. The
source and generated files were restored, no new episode or holdout was opened,
and the 35 N safety boundary remains unchanged. The diagnostic implementation
is retained with duplicate-key validation and correct complete-support-loss
semantics. Next work is a minimal upstream Genesis reproduction under a new
protocol, not model training. The synchronized Radeon tree compiled and passed
264 tests.

### Record 77: Reduce the failure twice and preserve both negative results

The upstream audit first excluded the recent MJCF armature bug as a candidate.
The locked Genesis revision already contains PR #3072, and Panda explicitly
authors armature 0.1 through its inherited default class. The equality warning
was traced to the generic `2 * substep_dt` sanitizer; the already rejected
0.010 s intervention was not scanned.

A preregistered static reproduction reconstructed the observed frame-196 hand
and parcel poses, reset every velocity, held the arm, and applied `[-20,-20] N`
for 64 physics steps. Stock and mass-aware conditions stayed near 5.08 N and
below 0.27 mm penetration with no registered divergence.

The next protocol added read-only full robot/parcel qpos, qvel, actual force,
and controller force. One source rerun exactly reproduced the original
162.186 N / 115.546 mm failure. Paired fresh scenes then restored the source
state with measured zero error and replayed the same nine-DOF force sequence.
Both stayed safe. Stock peaked at 10.586 N and mass-aware at 7.316 N; the only
registered difference was 5.491 N contact force at 198/3.

The result narrows the missing mechanism to state not represented by qpos,
qvel, or exposed post-step controller forces, such as PD targets/modes or
solver warm-start state. It does not justify a Genesis-wide bug claim. No
parameter, frame, episode, or holdout was scanned, and the 35 N gate remains
unchanged. The next step requires another protocol; visual/VLA work remains
behind the physical baseline gate.

The final synchronized Radeon tree compiled and passed all 268 tests.

### Record 78: Replay raw control inputs and close the observed adapter branch

The next preregistered unit added read-only access to Genesis `ctrl_mode`,
`ctrl_pos`, `ctrl_vel`, and `ctrl_force`. A pure validator partitions the nine
DOFs by mode, and the replay runner applies each recorded target through the
matching public position, velocity, or force API. Commit `63ac10b` froze the
protocol and implementation before any physical result was observed.

The one allowed source rerun exactly retained the candidate and failure. Its
64 events used seven position-mode arm joints and two force-mode fingers; only
the arm position targets changed, at the 30 Hz frame boundaries. The
mass-aware fresh-scene replay then reproduced the source failure at `203/4`,
162.186 N and 115.546 mm, with only float32-scale aligned-field differences.
This shows why post-step force replay failed and removes solver warm start as a
requirement for reproducing this event.

The stock cross-model reference reached 157.787 N and 115.544 mm at `198/1`.
The preregistered classifier therefore returned `invalid_reference`; a state
generated by the mass-aware dynamics is not a safe stock-model intervention.
No causal inertia claim, tuning, new episode, or holdout follows. The adapter
stays rejected and the project returns to stock-hand geometry planning and
candidate ranking.

One tooling pitfall was preserved: invoking pytest at repository root collects
two compatibility files named `test_capabilities.py` and causes an import-file
mismatch. The authoritative `pytest tests` scope passed 269 tests and 28
subtests; the duplicate-root collection error is not a failed assertion.

### Record 79: Freeze geometry-eligible candidate learning v2 before physics

V1 generated complete labels for only four of 12 train groups and one of six
development groups because label generation was tied to an observed reset
fallback. The v2 protocol changes the population without choosing on task
outcomes: all stock-hand boxes inside the existing height predicate activate
candidate planning, while collision-checked reset and every hard safety gate
remain enabled.

Commit `af88121` froze the selector and activation code first. The selector
then read deterministic randomization only and chose 32 train, 16 development,
and 16 holdout groups across four balanced profiles. A hash-bound audit
recomputed every sample and exact assignment. Radeon dry-run planning verified
192 maximum train and 96 maximum development rollouts, all with the frozen
`geometry-eligible` policy. A holdout request was rejected before planning.

The first audit exposed only a tuple/list JSON representation mismatch; the
comparison was normalized without changing evidence. The CLI summary also
gained the already-enforced activation policy field so dry-run artifacts are
self-describing. Train is now the only admissible physical split. Development,
model fitting, and the one-shot holdout remain sequential gates; vision/VLA
work remains paused.

### Record 80: Add a capacity-matched groupwise safety-first objective

The preregistered v2 comparison required a groupwise ranker, but the existing
trainer optimized four labels pointwise across all candidate rows. The new
objective retains the same 6,276-parameter network and feature schema. It
weights physical episode groups equally, ranks every safe candidate ahead of
force-aborted candidates, and ranks successful candidates ahead of failures
only within the safe set. Pointwise probability, force, and duration losses
remain for calibration. The pointwise baseline is behaviorally unchanged.

Pure tests verify stable grouping and that no pair crosses an episode or lets
success override safety. A five-step ROCm smoke on the first two completed
train groups produced a valid HIP 7.2 checkpoint in 1.39 seconds. In-sample it
avoided both static safety aborts and recovered one success, but this is only
wiring evidence; it is explicitly excluded from model selection. Exact model
hyperparameters will be frozen before development is run, and holdout remains
closed.

### Record 81: Freeze model recipes and the development promotion gate

Before the complete train collection existed, the project froze exactly two
capacity-matched recipes: pointwise and groupwise safety-first. Both use 28
features, 6,276 parameters, 2,000 steps, learning rate 0.001, weight decay
0.0001, seed 42, and one Radeon. The six relevant implementation files and
the collection protocol are bound by SHA-256 in a separate model-selection
TOML.

Evaluation now records paired success gains/losses, safety-abort reductions/
regressions, selected force and duration, and the same metrics per profile.
The promotion gate cross-checks profile totals against aggregate totals. It
requires all 16 development groups, four groups per profile, no profile safety
regression, aggregate task or safety improvement, and a six-candidate warm P95
below 5 ms. Eligible candidates use a fixed safety-first tie-break; if neither
passes, development cannot be reused for tuning and holdout stays closed.

The protocol audit, 18 directed tests, and an independent runtime parameter
count all passed on Radeon. No development scene or holdout was opened.

### Record 82: Make the train-before-development order executable

A two-phase orchestrator now turns the frozen model protocol into one command
per phase. The train phase refuses any existing development/holdout manifest,
requires the complete 32-group collection, trains both recipes, validates every
frozen hyperparameter plus AMD/HIP metadata, and writes a non-overwritable
checkpoint freeze manifest. The development phase verifies those checkpoint
hashes, rejects any existing holdout manifest, builds the combined dataset,
evaluates both models, and applies the fixed promotion gate without opening
holdout.

Tests cover capacity-matched command construction, physical-group rather than
row counts, and cross-split group rejection. The runner also hashes itself in
each result, so orchestration changes cannot be hidden. This is workflow
enforcement only; it does not add a third model or alter the frozen recipes.

### Record 83: Complete train collection and freeze checkpoints before development

One Radeon completed all 32 v2 train groups: eight from each of four profiles,
six candidates per group, 192 complete closed-loop rollouts, and zero failed
groups. Independent validation found no duplicate episodes, missing files, or
duplicate candidates and confirmed that neither a development nor holdout
manifest existed. SHA-256 binds the train manifest, log, and dataset. The 226
MiB full traces remain in the Radeon workspace rather than normal Git.

The frozen orchestrator then built a 192-row, 28-feature dataset and trained
pointwise and groupwise-safety-first under HIP 7.2. Both have 6,276 parameters,
2,000 steps, and seed 42. On train, static selection produced seven successes
and 17 safety aborts; reconstructed pointwise selection produced 12/4 and
groupwise produced 10/4. These are fitting and evaluation wiring results, not
model-selection evidence. Independent checks verified the checkpoint,
summary, dataset, collection protocol, model protocol, and pipeline hashes;
the freeze status is `train_checkpoints_frozen_before_development`.

Only after that record existed was one 16-group development collection
started; holdout still did not exist. Development outcomes therefore cannot
change capacity, objective, step budget, or checkpoints. PyTorch's
`device=cuda` value is its ROCm compatibility namespace; the physical device
is an AMD Radeon under HIP 7.2. The bilingual result and machine-readable
index are in `docs/GRASP_SCORER_V2_TRAIN_FREEZE_RESULTS.md` and
`evidence/training/grasp-scorer-v2-train-evidence.json`.
