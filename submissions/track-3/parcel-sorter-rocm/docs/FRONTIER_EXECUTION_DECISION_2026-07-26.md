# Frontier Execution Decision: Geometry First, Learning Second

Status date: 2026-07-26. This is an execution record, not a capability claim.
It translates the current evidence, recent open robotics work, and the
single-Radeon constraint into a staged experiment programme. Outcomes remain
unknown until the referenced frozen protocols complete.

## 1. Current evidence boundary

The local source tree passes 323 deterministic tests (one optional test is
skipped). The 128-sample cylinder candidate audit passed without constructing
a scene or reading task outcomes. It proves deterministic candidate coverage,
not IK reachability, grasp stability, or sorting success. The 24-sample ROCm
IK/FK/mesh-collision screen is frozen but must wait for the V5 controller probe
to release the only Radeon GPU.

V5 is an independent confirmation of a dynamic safety veto for rigid boxes.
Its outcome cannot be used before the runner produces the frozen result file.
Even a V5 pass authorizes only an online parallel-probe experiment; it does not
authorize enabling the veto in the production controller.

## 2. Research decisions

| Candidate | What it actually provides | Single-Radeon decision |
| --- | --- | --- |
| Geometry-aware candidate planning | Attributable IK, FK, collision, manipulability, and retry decisions | Primary paper method; finish static and closed-loop evidence first |
| RGB-D analytic geometry | Shape, pose, and size estimates with measurable error | First perception method after the planner works with privileged geometry |
| ACT RGB/RGB-D | Low-data action chunking already integrated through LeRobot | Formal learned baseline after the balanced-data gate |
| Compact Diffusion Policy | Multimodal action distribution with higher inference cost | Matched comparison after ACT; vary denoising steps only after a fixed checkpoint |
| VLA-Adapter 0.5B | A tiny language-conditioned policy implementation, not a parcel checkpoint | Preferred VLA compatibility spike; LoRA/action-head tuning only after license and ROCm audits |
| OpenVLA-OFT 7B | Continuous action chunks and strong reference implementation | Reference only initially; reported inference needs about 16-18 GB and the stack is CUDA-oriented |
| VLA evaluation harness | Reproducible model-server/benchmark separation and sharded evaluation | Reuse protocol ideas; it is not a model, does not include this Genesis task, and its published containers are CUDA-based |
| Force-memory VLA ideas | Force history can disambiguate contact states hidden from vision | Implement first as compact force tokens for the candidate selector, not as a full VLA replacement |
| Learned world models | Predictive latent/video dynamics for longer-horizon control | Defer until rigid-body geometry and closed-loop control are no longer the dominant errors |
| ROS 2 / MoveIt 2 | Deployment and replay interfaces | Add after algorithm freeze; do not present middleware as the core method |

The hard 35 N supervisor, geometric capability gate, and end-effector contract
remain outside every learned model. A language model may select a task or a
candidate family, but it may not bypass IK, collision, force, or aperture
checks.

## 3. Multi-shape parcel population

The current catalog contains twelve parallel-jaw training strata: ten box
strata from 60 x 35 x 25 mm micro parcels through 420 x 79 x 180 mm large
narrow cartons, one upright canister stratum with 40-70 mm diameter and
60-160 mm height, and one horizontal mailing-tube stratum with 150-300 mm
length and 35-65 mm diameter. Mass, friction, yaw, delay, and observation noise
are randomized independently within the checked-in ranges.

Official carrier-size examples and larger rectangular, square, envelope, and
tube ranges are kept as evaluation-only capability boundaries. Their minor
axes exceed the Panda parallel-jaw aperture or require suction/cradle support.
They must be rendered and rejected with an explicit reason rather than counted
as parallel-jaw failures or falsely claimed as graspable.

This separation answers two different questions: whether the present hardware
can sort diverse parcels inside its physical envelope, and whether the system
can recognize objects outside that envelope and route them to another end
effector.

## 4. Frozen execution order

### Stage A: mechanism proof

1. Finish V5 and apply its preregistered pass/fail rule without reading partial
   candidate outcomes.
2. Run the 24-sample cylinder ROCm static screen. A pass requires at least 75%
   of each cylinder profile to have a feasible candidate, state restoration at
   or below `1e-7`, one HIP device, and screen P95 below 5 s.
3. If the screen passes, add cylinder candidate selection to an isolated
   closed-loop configuration. If it fails, modify candidates only in a new
   development protocol and preserve the failed result.
4. Run a small matched closed-loop cylinder screen before changing defaults.
   Static feasibility alone never promotes a controller.

### Stage B: paper main method

Use identical physical samples for three arms: the historical controller,
collision-checked reset, and collision-checked reset plus multi-shape
feasible-pose planning.

The existing 12-profile, five-episode-per-profile campaign remains an
elimination screen. For confirmation, freeze 30 unseen physical episode IDs
per supported profile. This yields 360 paired units per arm and prevents one
difficult carton from defining the entire paper. Success is primary; force
abort and drop are safety co-outcomes. Peak force, duration, planning latency,
and throughput are secondary.

The main method advances only when aggregate success improves, force aborts
and drops do not worsen, direction is consistent across shape strata, and no
easy profile shows a material regression. Report Wilson intervals, exact
paired McNemar tests, paired bootstrap effects, and profile-level results.

### Stage C: ablations and robustness

Run each ablation as a single controlled removal from the accepted method:
collision filtering, manipulability ranking, symmetric wrist candidates,
retry replanning, and the dynamic safety probe if V5 and its online experiment
both pass.

Use the same episode manifest and correct the confirmatory hypothesis family
with Holm's procedure. Robustness cells independently vary unseen dimensions,
mass, friction, yaw, camera noise, action delay, and mild external impulses.
Do not change several factors in one cell unless it is explicitly labelled as
a combined stress test.

### Stage D: perception

Compare privileged geometry, noise-corrupted geometry, and ROCm RGB-D geometry
on the same closed-loop episodes. The first front end is analytic:

```text
metric depth -> ROCm back-projection -> table removal -> parcel cloud
             -> oriented box/cylinder fit -> confidence
             -> unchanged candidate planner and safety supervisor
```

Report position, orientation, dimension, and shape errors before reporting
task success. A learned residual head is justified only if the analytic error
is systematic and there is enough held-out data to measure correction.

### Stage E: learned policies

Formal training starts only after at least 300 balanced successful RGB-D
episodes are available and a group-stratified train/development/holdout split
is frozen. Train ACT RGB and ACT RGB-D for three seeds on the identical split,
then compact Diffusion RGB-D. Select checkpoints by development closed-loop
success, not offline loss, and evaluate each selected seed on at least 60 fixed
held-out episodes.

VLA-Adapter enters only after an isolated ROCm smoke verifies every operator,
the base/checkpoint/dependency licenses are recorded, and the action/state
adapter is lossless. Start with LoRA or the action expert, gradient
accumulation, AMP, and one task instruction. Compare it against ACT under the
same data and supervisor; do not compare a pretrained LIBERO checkpoint to a
parcel-specific policy as if the data were equivalent.

## 5. GPU optimization plan

Every accepted model receives the same optimization ladder: an eager FP32
correctness reference; AMP with numerically checked output and unchanged task
results; a batch/gradient-accumulation sweep under the 48 GB memory ceiling;
synchronized warm P50/P95 latency and peak VRAM; `torch.compile` or fused
kernels only after ROCm verification; and environment sharding or scene
cloning only after deterministic state equivalence is tested.

Optimize end-to-end task time, not kernel throughput alone. Report scene
build, first compilation, perception, planning, inference, physics, rendering,
and cleanup separately. Reject an optimization that improves speed while
reducing success or weakening the 35 N boundary.

## 6. Stop rules and paper-ready definition

The project is paper-ready only when there is a positive multi-profile main
comparison on unseen paired episodes, complete mechanism ablations and failure
taxonomy, at least one perception comparison that removes privileged parcel
pose, three-seed ACT RGB/RGB-D results plus one matched stochastic-policy
result (or an explicit failed data gate), ROCm performance evidence, immutable
configs/manifests/hashes, bilingual methods and results, and explicit
simulation/end-effector limitations.

If the final planner does not improve unseen closed-loop success, the positive
method paper is stopped. The alternative is a larger negative-result benchmark
on safety interventions and failure mechanisms; existing development episodes
must not be relabelled as confirmatory data.

## 7. Retrieval provenance

Access date: 2026-07-26. OpenAlex was queried with three bounded searches using
`GET /works`, `filter=from_publication_date:2023-01-01,has_abstract:true`,
`sort=relevance_score:desc`, and `per_page=8`. Queries covered parcel sorting,
geometry/collision-constrained grasping, and VLA/world-model manipulation.
GitHub metadata and README files were retrieved through the repository API for
`allenai/vla-evaluation-harness`, `OpenHelix-Team/VLA-Adapter`, and
`moojink/openvla-oft`.

Primary references include ACT (RSS 2023, DOI
`10.15607/RSS.2023.XIX.016`), OpenVLA (arXiv `2406.09246`), OpenVLA-OFT
(arXiv `2502.19645`), and VLA-Adapter (arXiv `2509.09372`). Repository claims
establish candidate existence, not Radeon compatibility or effectiveness in
this project; both require project-local evidence.
