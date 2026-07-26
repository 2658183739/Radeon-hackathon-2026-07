# Mobile Harness-Lite and Self-Improvement Result (2026-07-27)

## Scope and claim boundary

This result covers the mobile dual-Franka embodiment, a three-cup physical
suction tool, a right-arm V-cradle, a 1600-step SmolVLA checkpoint, an offline
Harness-Lite ablation, failure-to-curriculum conversion, and one controlled
closed-loop run on a single AMD Radeon `gfx1100` with ROCm 7.2.1. SmolVLA
actively controls bounded base-velocity residuals during grasp approach and
transport. The 240 Hz expert loop still controls arm IK, contact, suction,
lift, and placement. This is not yet autonomous full-action VLA control or a
generalization claim.

## System

- Physics: Genesis World 1.2.3 at 240 Hz on one Radeon GPU.
- Embodiment: 3-DoF holonomic base and two 7-DoF Franka Panda arms.
- Tools: left three-cup compliant suction; right passive V-cradle.
- Policy: LeRobot SmolVLA initialized from
  `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`.
- Inputs: 224x224 overhead RGB, 43-D non-privileged state, task text.
- Output: 19-D base and dual-arm Cartesian action.
- Slow-fast control: 3 Hz VLA/Harness and 240 Hz deterministic safety loop.

Metric depth is recorded but is not an input to this checkpoint. The successful
run used the left suction arm; cooperative load sharing by the right cradle is
not yet validated.

## Harness-Lite

The expert supplies the nominal action. SmolVLA supplies a residual. Five
candidate scales (`0, 0.25, 0.5, 0.75, 1.0`) are generated and verified. The
selected candidate must satisfy 5 cm/s base speed, 1 rad/s yaw rate, 4 cm
Cartesian step, 1 cm position residual, 5 degree quaternion residual, 50%
expert-progress, finite-value, and 35 N force gates. Tool commands are copied
from the stage-aware expert because a sign error can immediately drop a parcel.
An invalid VLA action falls back to the expert. A force violation stops the
base, holds both arms, and releases suction.

## Dataset and training

Six parameterized expert trials produced four successes and two lift failures.
The merged training set contains four episodes and 2,601 frames. The successful
profiles are a standard carton, an offset light carton, a flat mailer, and a
low-friction electronics box. The 0.55 kg and 0.65 kg cartons failed during
lift without crossing the 35 N force limit.

SmolVLA trained for 1,600 steps (4.92 epochs), batch 8, four workers, and AMP.
Loss fell from 2.062 to 0.063. Steady data throughput reached about 60
samples/s and peak allocated memory was about 2.21 GB. The checkpoint is about
865 MB.

## Offline ablation

All results use the middle frame of each episode-stage pair: four episodes by
six stages, or 24 samples. Each policy queue is reset and each seed is fixed.

| Variant | Mean action MAE | Envelope pass | Notes |
| --- | ---: | ---: | --- |
| Raw SmolVLA | 0.022817 | 0/24 | unsafe absolute targets and non-binary tools |
| Safety-clipped SmolVLA | 0.019601 | 24/24 | numeric limits only |
| Harness-Lite | 0.005947 | 24/24 | 97.9% mean selected scale; 3 tool corrections |
| Expert through same executor | 0.004538 | 24/24 | executor reference, not zero-error oracle |

Harness-Lite reduced MAE by 73.9% relative to raw SmolVLA while keeping every
sample inside the execution envelope. This is offline action agreement, not a
task-success rate.

## Online matched runs

| Run | VLA actuation | Result | Placement error | Diagnostic |
| --- | --- | --- | ---: | --- |
| Shadow v1 | none | success | 1.19 cm | 110 calls; all six stages |
| Base residual v1 | base | failure at grasp | n/a | reused prior VLA action as nominal; causal wiring defect |
| Base residual v2 | base | success | 0.92 cm | 70 calls; 3,563 applied physics steps |

The successful v2 run lifted, transported 30 cm, placed, and released the 0.4
kg carton. It had zero suction breaks, 11.80 N peak suction force, and 9.62 N
peak contact force. Harness selected a mean scale of 0.939, used no full expert
fallback or emergency stop, and corrected six tool-command signs. Cold-start
latency was 1,048 ms; warm mean/P95 latency was 207.04/213.25 ms. The earlier
5 Hz target lacked timing margin, so the verified controller uses 3 Hz.

## Failure-driven improvement

`build_mobile_failure_replay.py` converts failed collection results into a
ranked, auditable curriculum without touching holdouts or promoting weights.
The first manifest ranks the 0.65 kg and 0.55 kg lift failures and proposes
0.585 kg and 0.495 kg bridge trials. Collection, retraining, independent
closed-loop evaluation, and checkpoint promotion remain separate gates. This
is a safe batch self-improvement cycle, not unbounded online weight mutation.

## Literature-informed decisions

Three recent preprints informed the design, without being copied or claimed as
reproduced: DEED (arXiv:2607.20345) motivates experience-driven post-training;
Seed2Scale (arXiv:2603.08260) motivates collector-verifier-target separation;
PACT (arXiv:2606.08414) motivates constraint-aware post-training and bounded
policy shift. We adopt failure memory, explicit verification, curriculum
bridges, and quarantined promotion. We do not adopt automatic reward labeling,
large-model scoring, or direct constraint-gradient distillation in this
checkpoint.

Retrieval provenance: arXiv API `https://export.arxiv.org/api/query`, queries
over `cat:cs.RO` with self-improving, self-evolving, experience-driven,
failure-replay, and vision-language-action terms; first page only; accessed
2026-07-27.

## Iteration 2: mass-aware expert and frozen holdout

Failure diagnosis showed that the 0.55 kg and 0.65 kg parcels remained attached
but missed the 8 cm lift gate by only 1.1--2.6 mm because the arm tracked a
fixed 10 cm target less accurately under load. The success criterion was not
relaxed. Instead, the expert added a bounded mass-aware lift target from 10 to
12 cm and matched placement descent. Targeted reruns passed, and the unchanged
six-profile collection improved from 4/6 to 6/6 successes. The audited v2
dataset has 3,899 frames and all six stages in every episode.

SmolVLA v2 trained for 2,400 steps, preserving about 4.92 epochs after the data
increase. Training took 6 min 19 s, peaked at 2.21 GB, reached about 63
samples/s, and ended at loss 0.067. On 36 training episode-stage samples, the
precision-handoff Harness achieved MAE 0.005485 and 36/36 envelope passes,
versus 0.022105 and 0/36 for raw VLA.

The first five unseen runs produced 4/5 successes. Its only failure was then
used as development evidence: the VLA reduced the final approach speed until
the two-cup seal timed out, while the matched expert succeeded. A directional
progress gate alone did not fix it. The accepted slow-fast change hands control
fully to the expert when grasp-approach speed falls below 2.5 cm/s. The failed
case then succeeded with 1.32 cm placement error, seven explicit handoffs, and
no force violation.

Because that change used the first campaign, those five runs are labeled
development, not holdout. A new frozen v2 holdout changed size, mass, friction,
and offset again. It achieved 4/5 successes (80% point estimate), 0 force
violations, and 4/5 runs with VLA base actuation. The 95% Wilson interval is
37.55%--96.38%, so this is only a small-sample gate. The 0.72 kg boundary box
failed before latch and generated a quarantined 0.648 kg curriculum bridge.
No parameter was changed after the frozen v2 result.

## Remaining gates

The subsequent self-improvement cycle expanded the frozen protocol to 100 trials:
v2 scored 96/100 and v3 scored 91/100 and was not promoted. A new 100-trial
paired arm-residual holdout also preserved 94/100 success but failed the placement
accuracy gate, so the mode remains disabled. Right-cradle cooperation, unseen
geometry, and sim-to-real remain unverified; the completed RGB-D ablation retained RGB.

## Evidence

All compact evidence is under `evidence/mobile_bimanual/multiprofile_v1/`.
Success and failure records are both retained. Model weights and the full
dataset remain on the Radeon workspace and are identified by path and hashes.
