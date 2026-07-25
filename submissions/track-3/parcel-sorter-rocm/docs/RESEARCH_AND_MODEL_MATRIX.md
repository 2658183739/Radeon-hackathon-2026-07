# Research and Open-Model Decision Matrix

Access date: 2026-07-25. Scope: targeted retrieval for a single-Radeon,
open-source parcel-sorting system. A code license is not treated as a model or
dataset license; every selected checkpoint still needs a recursive license and
dependency audit before it enters the reproducible release.

## Decision

The implementation order is:

1. collect a corrected, balanced RGB-D dataset and keep ACT as the controlled
   baseline;
2. train compact Diffusion Policy on the identical split;
3. compare RGB and RGB-D for both policies in the same closed loop;
4. run a ROCm compatibility spike for VLA-Adapter 0.5B;
5. add a native point-cloud policy only if the RGB-D ablation shows a useful
   depth signal and the 2-D encoding becomes the limiting factor.

This order maximizes scored robot capability and Radeon evidence before adding
model size. The present 96 successful episodes are not enough to justify a
generalist VLA claim.

## Method matrix

| Method | Open artifacts | Fit for this project | Radeon status | Decision |
| --- | --- | --- | --- | --- |
| ACT | MIT reference; Apache-2.0 LeRobot implementation | Strong low-data action-chunking baseline; already integrated | 5,000-step training and closed-loop inference verified | P0 baseline; retrain with corrected data and 3 seeds |
| Diffusion Policy | MIT reference; LeRobot implementation | Strong multimodal action distribution, but iterative denoising adds latency | Compact 76.6M one-step training verified | P0 comparison; sweep 5/10/20 denoising steps |
| 3D Diffusion Policy (DP3) | MIT code; RSS 2024 paper | Native point cloud can exploit geometry better than a depth image | No ROCm evidence in this repository | P1 only after RGB-D ablation and operator audit |
| RISE | Public 3D-policy repository; IROS 2024 paper | Sparse 3D tokens fit parcel geometry and occlusion | GitHub API does not declare a license; ROCm unverified | Research only until license and sparse-operator audits pass |
| FlowPolicy | MIT repository; AAAI 2025 paper | Fast 3D flow matching may reduce iterative diffusion cost | ROCm and the current action interface are unverified | P1 after ACT/Diffusion; compare with DP3 under one budget |
| Consistency Policy | Public paper and code ecosystem | Distillation can reduce diffusion inference latency | Not integrated | P2 if Diffusion succeeds but misses latency target |
| VLA-Adapter 0.5B | MIT repository; public MIT-tagged base/checkpoints | Language-conditioned, 0.5B, reported 10-48 GB training configurations | Official setup is CUDA-oriented; ROCm unverified | Preferred VLA compatibility spike |
| SmolVLA | Apache-2.0 LeRobot code; public checkpoint | Native LeRobot path and compact architecture | Entry exists; checkpoint unavailable on the Radeon host | Hold: checkpoint metadata did not declare a license |
| OpenVLA / OpenVLA-OFT | MIT code and published weights | Strong VLA research baseline; OFT improves action throughput | Official examples use CUDA/FlashAttention; 7B is unnecessary for one instruction | Research-only; weights inherit Llama 2 terms |
| Octo | MIT code; 800k-trajectory generalist policy | Useful open generalist reference | JAX ecosystem adds avoidable ROCm risk | Research-only |
| RDT-1B | MIT code and MIT-tagged checkpoint | Open 1B diffusion foundation model | Bimanual embodiment and custom stack mismatch | Compatibility fallback, not the first VLA |
| openpi (pi0/pi0.5) | Apache-2.0 code and public checkpoints | Strong frontier reference | Official README requires NVIDIA GPU; full tuning exceeds this card | Excluded from competition implementation |
| NVIDIA GR00T | Apache-2.0 code; NVIDIA model license | Broad embodiment support | NVIDIA/CUDA-oriented and model terms differ from code | Excluded from the strict open Radeon path |

"Open" in this table describes the cited artifact, not automatic approval for
submission. VLA-Adapter must still pass a transitive audit of Qwen2.5,
DINOv2/SigLIP, wheel sources, and checkpoint files before use.

## Capability optimization plan

| Capability | Next experiment | Frozen controls | Acceptance evidence |
| --- | --- | --- | --- |
| Simulation | profile physics and camera separately; keep rolling friction scoped | catalog, seeds, 35 N limit | steps/s, render Hz, task regression |
| Learning | 300 successful catalog-v2 episodes, ACT and compact Diffusion, 3 seeds | split, action contract, training budget | held-out closed-loop mean and range |
| Robustness | curriculum plus failure-neighbour collection; nominal/in-domain/unseen suites | episode manifest and safety boundary | per-profile success, drop and recovery |
| Closed loop | contact-aware speed shaping and residual correction outside the learned action | supervisor and force abort | first-attempt success and recovery without force regression |
| GPU optimization | AMP/batch sweep, synchronized latency, copy/render profile, then compile | model, seed and dataset | samples/s, P95, peak VRAM, success |
| Multimodal | RGB versus RGB plus derived depth view; later point cloud | same episodes/checkpoint schedule | unseen-profile delta and latency cost |

The first model promotion gate is at least 30 held-out episodes per candidate;
the final comparison should use at least 60 predeclared episodes, profile-level
reporting, three training seeds, fixed 35 N safety, and artifact hashes.

## Retrieval provenance

Targeted OpenAlex queries used `GET https://api.openalex.org/works` with
`search`, `filter=from_publication_date:2022-01-01`,
`sort=relevance_score:desc`, and `per_page=5` or `8`. Queries covered action
chunking, Diffusion Policy, 3D Diffusion Policy, VLA, OpenVLA, RDT-1B,
VQ-BeT, and Consistency Policy. GitHub repository metadata came from
`GET https://api.github.com/repos/{owner}/{repo}`; selected README files came
from the GitHub contents API. Checkpoint metadata came from
`GET https://huggingface.co/api/models/{model_id}`.

Primary papers and identifiers:

- ACT: Zhao et al., *Learning Fine-Grained Bimanual Manipulation with Low-Cost
  Hardware*, RSS 2023, DOI `10.15607/RSS.2023.XIX.016`.
- Diffusion Policy: Chi et al., RSS 2023, DOI
  `10.15607/RSS.2023.XIX.026`.
- DP3: Ze et al., RSS 2024, DOI `10.15607/RSS.2024.XX.067`, arXiv `2403.03954`.
- Consistency Policy: Prasad et al., RSS 2024, DOI
  `10.15607/RSS.2024.XX.071`.
- RISE: IROS 2024, DOI `10.1109/IROS58592.2024.10801678`.
- FlowPolicy: AAAI 2025, DOI `10.1609/AAAI.V39I14.33617`.
- DROID: RSS 2024, DOI `10.15607/RSS.2024.XX.120`.
- Octo: Ghosh et al., RSS 2024, DOI `10.15607/RSS.2024.XX.090`.
- OpenVLA: Kim et al., arXiv `2406.09246`.
- OpenVLA-OFT: Kim et al., RSS 2025, DOI `10.15607/RSS.2025.XXI.017`.
- SmolVLA: Shukor et al., arXiv `2506.01844`.
- RDT-1B: Liu et al., arXiv `2410.07864`.
- VLA-Adapter: Wang et al., arXiv `2509.09372`, AAAI 2026 DOI
  `10.1609/aaai.v40i22.38931`.

Repository and model pages used for compatibility/license facts:

- https://github.com/tonyzhaozh/act
- https://github.com/real-stanford/diffusion_policy
- https://github.com/YanjieZe/3D-Diffusion-Policy
- https://github.com/huggingface/lerobot
- https://github.com/OpenHelix-Team/VLA-Adapter
- https://github.com/openvla/openvla
- https://github.com/Physical-Intelligence/openpi
- https://github.com/NVIDIA/Isaac-GR00T
- https://huggingface.co/Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b
- https://huggingface.co/VLA-Adapter/LIBERO-Spatial-Pro

## Verified retrieval snapshot

The following targeted requests were repeated for this work session rather than
copied from a secondary list. The arXiv export API returned the paper title and
publication date for every identifier; the GitHub API returned repository
license metadata. These facts select experiments, but they do not prove task
performance or transitive license compatibility.

| Artifact | Retrieval result | Engineering consequence |
| --- | --- | --- |
| ACT, arXiv `2304.13705` | *Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware*, published 2023-04-23 | Keep action chunking as the low-data baseline |
| Diffusion Policy, arXiv `2303.04137` | *Diffusion Policy: Visuomotor Policy Learning via Action Diffusion*, published 2023-03-07 | Train the matched stochastic-action comparison |
| DP3, arXiv `2403.03954` | *3D Diffusion Policy: Generalizable Visuomotor Policy Learning via Simple 3D Representations*, published 2024-03-06 | Defer native point clouds until depth-view ablation is positive |
| Consistency Policy, arXiv `2405.07503` | *Consistency Policy: Accelerated Visuomotor Policies via Consistency Distillation*, published 2024-05-13 | Use only if Diffusion latency fails the gate |
| OpenVLA, arXiv `2406.09246` | *OpenVLA: An Open-Source Vision-Language-Action Model*, published 2024-06-13 | Research reference; weight terms and CUDA stack need separate audit |
| Octo, arXiv `2405.12213` | *Octo: An Open-Source Generalist Robot Policy*, published 2024-05-20 | Research reference; JAX/ROCm is a separate risk |
| RDT-1B, arXiv `2410.07864` | *RDT-1B: a Diffusion Foundation Model for Bimanual Manipulation*, published 2024-10-10 | Compatibility fallback, not the first single-arm route |
| pi0, arXiv `2410.24164` | *$\\pi_0$: A Vision-Language-Action Flow Model for General Robot Control*, published 2024-10-31 | Frontier reference; official NVIDIA constraint keeps it outside the main path |
| SmolVLA, arXiv `2506.01844` | *SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics*, published 2025-06-02 | Hold until checkpoint license is explicit |
| RISE, IROS 2024 | *RISE: 3D Perception Makes Real-World Robot Imitation Simple and Effective* | Sparse 3D encoder candidate; current license gate fails |
| FlowPolicy, AAAI 2025 | *FlowPolicy: Enabling Fast and Robust 3D Flow-Based Policy via Consistency Flow Matching for Robot Manipulation* | Candidate after RGB-D benefit and a matched latency budget are established |
| DROID, RSS 2024 | *DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset* | Supports diversity-first collection; not directly reusable for this embodiment |
| AXIS, arXiv `2607.21588` | *AXIS: A Growable Community-Driven Data Engine for Scalable Robot Manipulation* | Very recent data-engine signal, not evidence for this task |
| Bias-aware collection, arXiv `2607.21582` | *Scale Up Strategically: Learning Compositional Generalization via Bias-Aware Evaluation and Data Collection for Robotic Manipulation* | Motivates failure-stratified recollection after the frozen baseline |
| `huggingface/lerobot` | GitHub API: Apache-2.0, default branch `main` | Use pinned LeRobot policy/data interfaces |
| `OpenHelix-Team/VLA-Adapter` | GitHub API: MIT, default branch `main` | Candidate for isolated ROCm and recursive-license spike |

## 2026 hierarchical planning and world-model audit

This audit was performed while the frozen geometry campaign was running; it
does not alter the current method or allocate GPU time away from it.

| Method | Retrieved evidence | Project fit | Decision |
|---|---|---|---|
| 3D HAMSTER, arXiv `2606.31329` | RGB-D and language to metric 3D end-effector trajectories; the paper integrates them with a point-cloud low-level policy | Architecturally matches a future high-level planner above the existing safety controller | Research hold: repository root had no verifiable license and the released repository did not contain the paper's low-level policy at audit time |
| SeededGrasp, arXiv `2607.20207` | VLM predicts a semantic seed point and a lightweight geometric model generates grasps; abstract reports 2.5M grasps, 72% simulation success, and 78% real success | Strongest conceptual match for adding language without replacing geometric execution | License/code-completeness gate not passed; use only as a paper baseline until repository and data terms are audited |
| V2F, arXiv `2607.19804` | Vision-derived geometry plus a physics-informed residual network predicts a safe grasp-force envelope | Relevant future innovation for fragile parcels and damage-aware scoring | Defer until rigid parcel geometry succeeds; requires compliant material labels and a damage metric not present in the current task |
| RoboInter1.5, arXiv `2607.18709` | Intermediate representations connect VQA, VLA execution, grasp/contact/motion annotations, and conditioned world prediction | Supports a modular plan-then-execute design and interpretable training targets | Research only: too recent for a stable dependency baseline; repository search reported MIT but checkpoints, datasets, and transitive terms remain unaudited |

The engineering consequence is conservative. A large end-to-end VLA or world
model is not the next control intervention. If the risk-gated geometric method
passes confirmation, the first learned extension should predict a semantic or
visual seed while retaining audited IK, collision filtering, 35 N force abort,
and deterministic recovery. A world model may later rank or simulate candidate
outcomes, but it must not bypass the safety supervisor.

Retrieval provenance, accessed 2026-07-25:

- arXiv export `GET /api/query?id_list=2606.31329` for 3D HAMSTER;
- arXiv export topic query `cat:cs.RO AND all:"grasp pose" AND
  (all:collision OR all:feasibility)`, sorted by submission date, which returned
  SeededGrasp, V2F, and RoboInter1.5;
- GitHub repository search for `SeededGrasp` and `RoboInter`; repository-core
  API quota was then exhausted and raw README retrieval timed out. Those gaps
  are recorded as license/completeness blockers, not treated as approval.
| `Physical-Intelligence/openpi` | GitHub API: Apache-2.0, default branch `main` | Keep as reference; README's NVIDIA requirement is disqualifying for the main path |
| `Genesis-Embodied-AI/Genesis` | GitHub API: Apache-2.0, default branch `main` | Continue Genesis physics/rendering path |

The retrieval commands and exact outputs are summarized here so a learner can
repeat them without treating search snippets as evidence:

```text
GET https://export.arxiv.org/api/query?id_list=2304.13705,2303.04137,2403.03954,2405.07503,2406.09246,2405.12213,2410.07864,2506.01844,2410.24164
GET https://api.github.com/repos/{owner}/{repo}
```

## Parcel geometry evidence

The catalog separates measured carrier products from hardware-feasible training
strata. USPS product pages provide exact box dimensions already encoded in the
evaluation-only profiles; USPS Notice 123 provides the official length/girth
boundary used for the larger tube stress range. FedEx and UPS packaging pages
are retained as qualitative packaging references, not as invented exact product
dimensions. A profile is never described as carrier-standard unless its source
gives a dimension.

| Geometry class | Representative source or rule | Catalog treatment |
| --- | --- | --- |
| Small/medium/large rectangular box | USPS Small, Medium, and Board Game Flat Rate product pages | Exact evaluation-only boxes plus broader `small_carton` to `large_narrow_carton` training strata |
| Flat mailer | USPS flat-rate packaging family | Rigid flat-mailer proxy; deformable mailer remains future work |
| Upright cylinder | Consumer canister/tube geometry within the Panda aperture | Training profile with radius/height randomization |
| Horizontal cylinder | USPS nonstandard cylindrical-mail rule and tube dimensions | `mailing_tube` training profile plus `large_mailing_tube` boundary profile |
| Oversize box | USPS board-game box and length/girth rules | Evaluation-only until suction or a cradle end-effector is implemented |

Sources:

- https://store.usps.com/store/product/priority-mail-flat-rate-small-box-P_SMALL_FRB
- https://store.usps.com/store/product/priority-mail-flat-rate-medium-box-1-P_O_FRB1
- https://store.usps.com/store/product/priority-mail-board-game-large-flat-rate-box-GB_FRB
- https://pe.usps.com/text/dmm300/Notice123.htm
- https://www.fedex.com/en-us/shipping/packaging.html
- https://www.ups.com/us/en/supplychain/resources/glossary-term/ups-packaging-guidelines.page

Warnings: citation counts and repository activity are time-dependent. GitHub
license metadata describes the repository, not all weights or dependencies.
No candidate is considered ROCm-compatible until it executes on the target
Radeon and produces a retained log.

The 2026 arXiv entries above are frontier signals, not stable baselines. They
are used only to refine data-collection experiments and do not bypass the
repository-license, ROCm, or held-out-evaluation gates.

## Matched model-selection protocol

The ranker now rejects comparisons whose checkpoints were not evaluated on
identical episode sets, randomized-sample SHA-256 fingerprints, or contact-force
thresholds. It reports Wilson 95% intervals and per-profile success summaries,
then ranks by:

1. zero/minimum safety-violation rate;
2. macro-average profile success, so a dominant box class cannot hide tube or
   large-parcel failures;
3. overall success, drop rate, P95 latency, and peak contact force.

This is an evaluation improvement, not a model-performance claim. New results
remain pending until Radeon collection, training, and held-out execution finish.

## Approach-safety research and current tradeoffs

| Source | Reusable idea | Current project choice |
| --- | --- | --- |
| OSCBF, arXiv `2503.06736`, StanfordASL, MIT | Add an operational-space CBF safety filter around a nominal controller at high rate | Do not import its JAX/URDF stack; retain the principle that safety filtering preserves the policy interface |
| Collision Cone CBF, arXiv `2503.00623` | Combine relative-motion collision-cone constraints with Cartesian impedance | Start with Genesis fingertip AABB clearance, then add velocity terms |
| RL-enhanced CBF, arXiv `2211.11391` | Tune barrier parameters from data rather than learning unconstrained actions | Freeze thresholds for matched A/B first; no tuning before the expert safety gate |

The two negative controls show that frame-level force braking is too late and
that enlarging vertical recovery steps can break successful trajectories. The
next candidate is a Genesis fingertip-AABB pre-contact filter that logs gap,
filter count, latency, and GPU synchronization cost. It is an engineering
filter, not a formal safety proof, and does not replace the 35 N hard abort.

## Loaded-stability and recovery research audit

The snapshot and regrasp probes narrow the next research question: static pose
feasibility and a 30 mm loaded test do not predict full transport, while
execution-state recovery needs a materially different support condition. The
following papers are architecture signals only; no repository, weight, dataset,
or transitive license from this table is approved for the submission.

| Source | Relevant idea | Project decision |
| --- | --- | --- |
| GraspIT, arXiv `2607.05869` | Pair RGB-D observations with physics-validated SE(3) grasp annotations | Candidate data design for future grasp ranking; first audit code/data licenses and prove Radeon execution |
| Physical Agentic Loop, arXiv `2604.07395` | Surface slips, stalls, and empty grasps as structured execution state for replanning | Closest architectural match to the new recovery states; retain deterministic safety supervision below any language layer |
| ShapeGrasp, arXiv `2605.02347` | Iteratively combine visual, tactile, and proprioceptive feedback with shape completion | Relevant only after a modeled open-source tactile sensor exists; current force/contact telemetry is not equivalent to tactile input |
| DeepSimHO, arXiv `2310.07206` | Use physics to validate stable interaction poses instead of proximity alone | Supports simulator-based stability checks, but the project must extend beyond the rejected short horizon |
| TouchWorld, arXiv `2607.07287` | Predict contact evolution and react to slip, misalignment, and force mismatch | Longer-term tactile-world-model direction; not a current dependency or result claim |
| Grasp to Act, arXiv `2602.20466` | Optimize grasps for downstream dynamic forces rather than static geometry alone | Strongest objective-level justification for transport-conditioned grasp scoring |

The implementation order is now: define a long-horizon loaded-stability target;
evaluate it on held-out full transports; only then consider a lightweight
learned scorer on PyTorch/ROCm. A VLA may select task intent or semantic target
later, but it must not bypass IK, collision checks, the 35 N abort, or explicit
recovery states. Metadata was checked through the arXiv API on 2026-07-26.

### Updated model decision after the full-task counterfactual

The formal counterfactual shows that the target is not “stable after direct
IK transport.” The useful label is the outcome of the real delayed,
feedback-controlled task. Candidate features should include parcel dimensions,
mass and friction, destination displacement, pose offsets, IK residual,
collision clearance, manipulability, and joint distance. Targets should be
multi-task: safety abort first, task success second, then peak force and
duration among safe successes.

Start with a small MLP or gradient-boosting baseline, not a VLA. The MLP can be
trained and inferred with PyTorch/ROCm, exported with its feature contract, and
kept behind deterministic feasibility and safety gates. RGB-D can later add
shape/material embeddings once the camera pipeline produces aligned labels;
language does not improve this low-level choice until the physical scorer has
held-out evidence.
