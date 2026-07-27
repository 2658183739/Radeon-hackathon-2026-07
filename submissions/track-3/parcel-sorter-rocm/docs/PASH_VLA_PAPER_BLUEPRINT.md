# PASH-VLA Paper Blueprint (Existing Evidence Only)

## Proposed title

**PASH-VLA: Payload-Aware Safety-Harness Vision-Language-Action Control for
Single-Radeon Mobile Bimanual Parcel Handling**

## Draft abstract

Mobile bimanual parcel handling combines vision-language decisions, long-horizon
motion, contact-rich manipulation, and strict safety constraints. Directly
executing absolute VLA actions can violate actuator envelopes, cause contact
impacts, or miss task deadlines. We present PASH-VLA, a payload-aware residual
VLA running on one AMD Radeon GPU with ROCm. SmolVLA proposes a 19-D base and
dual-arm action at 3 Hz, while a deterministic expert supplies the nominal
action at 240 Hz. A Harness evaluates five residual scales against velocity,
progress, inverse-kinematics, tool-interlock, and 35 N contact constraints.
PASH-VLA adds short-horizon force memory that reduces learned-policy authority
under sustained or rapidly rising loads, plus a deadline-liveness gate for
long-payload transport. Failed trajectories enter isolated bridge curricula for
near-line Radeon retraining; a candidate is promoted only after frozen task,
safety, actual-actuation, ROCm-provenance, and Wilson non-inferiority checks.
Three compliant suction cups and a physical V-cradle provide bimanual load
sharing. The retained SmolVLA v2 achieved 96/100 with zero 35 N violations on a
frozen four-profile parameter-randomized campaign, while failure-trained v3
scored 91/100 and was rejected automatically. In one 1.44 m extra-long-carton
development case, PASH-VLA completed an 8.52 cm lift, 30 cm transport, and
placement at 2.11 cm error with zero suction breaks. Force Memory tightened 11
of 68 inferences and requested two full expert fallbacks. The long-carton result
is mechanism evidence, not a generalization claim.

## Research questions

- **RQ1:** Does a bounded residual Harness produce more executable actions than
  raw VLA output or numerical clipping alone?
- **RQ2:** Can short-horizon contact-force memory suppress risky VLA actions
  without changing model weights or the hard safety limit?
- **RQ3:** Can failure-driven retraining with a frozen promotion gate implement
  near-line self-improvement that can also reject regressions?
- **RQ4:** Can tri-suction/V-cradle cooperation extend handling beyond the
  length envelope of one parallel gripper?
- **RQ5:** Can rigid-object projection and a deterministic metric-depth sidecar
  safely expose both learned arm proposals without degrading payload geometry?

## Method

Let `a_e` be the expert action and `a_v` the VLA proposal. The bounded residual
decision is

```text
r = Clip(a_v - a_e; residual limits)
a(alpha) = a_e + alpha * r
alpha in {0, 0.25, 0.50, 0.75, 1.0}
```

Every candidate must pass finite-value, base-velocity, Cartesian-step,
expert-direction progress, tool-stage interlock, IK, and 35 N hard-force gates.
If no learned candidate is safe, `alpha=0` selects the expert. Reaching the hard
force limit stops motion and enters the safety response.

For the latest `W=6` force observations `F[t-W+1:t]`, Force Memory computes

```text
r_load = max(0, (max(F) - F_soft) / (F_limit - F_soft))
r_rise = max(0, (F_t - min(F) - d) / (F_rise - d))
risk = min(1, max(r_load, r_rise))
alpha <= 1 - risk
```

The current development values are `F_soft=20 N`, `F_limit=35 N`, rise
deadband `d=2 N`, and full-fallback rise `F_rise=8 N`. PASH-v25 does not use
these values to claim statistical superiority.

The transport deadline gate is

```text
if remaining_distance > remaining_time * expert_forward_speed * capacity:
    latch expert control for the rest of transport
```

The cooperative-payload capacity ratio is `0.60`, derived from the independent
v20 expert run rather than tuned backward from v24 or v25 success.

## Three contributions

1. **PASH residual decision layer.** VLA proposals, expert progress, temporal
   force memory, and deadline liveness become one auditable candidate-selection
   problem instead of giving the VLA direct torque or tool authority.
2. **Rejectable multi-timescale self-improvement.** Within-rollout Force Memory,
   between-attempt primitive-gap/task-global memory, and between-campaign bridge
   curricula, Radeon retraining, frozen evaluation, and Wilson promotion remain
   isolated. Rejection of v3 is negative evidence that the guard works.
3. **Payload-aware mobile bimanual embodiment.** Three compliant cups and a
   physical V-cradle combine seal checks, persistent contact, incremental
   dual-arm IK, and stable placement confirmation for long rigid cartons.

## Results supported by current evidence

| Experiment | Result | Supported conclusion |
| --- | --- | --- |
| Raw SmolVLA, 36 stage samples | MAE 0.022105; 0/36 envelope passes | Raw actions are not directly executable |
| Harness-Lite, same samples | MAE 0.005485; 36/36 passes | Bounded residuals improve in-distribution action agreement |
| SmolVLA v2, frozen 100 trials | 96/100; zero force violations | Parameter robustness within four known profiles |
| Failure-bridge v3, same holdout | 91/100; Wilson gate failed | Promotion can reject a regressing candidate |
| RGB-D versus RGB, 42 stages | MAE +1.35%; latency +9.65% | More modalities did not improve this checkpoint |
| Left-arm residual, paired 100+100 | 94/100 versus 94/100; worse placement | The precision gate rejected excess action freedom |
| Cooperative chain v19-v24 | Two passes and four retained mechanism failures | Incremental IK, placement confirmation, and deadline gate form a causal chain |
| PASH-v25 mechanism case | Pass; 11 tightenings, 2 fallbacks, 0 emergency stops | Force Memory entered the Radeon loop without breaking this case |
| Adaptive-retry mechanism case | First attempt passed; 84 inferences and 30/30 left-arm IK | Primitive/task-global memory path ran on Radeon; no retry-benefit claim yet |
| Dual-arm depth-sidecar mechanism case | Pass; 24/24 material left/right updates, 2,356 arm-residual physics steps, 0 m span change | Both VLA arm proposals entered the Radeon loop under rigid projection; one case only |

## Planned paper figures and tables

- **Figure 1:** RGB/state/text, SmolVLA, Force Memory, Harness, expert fast loop,
  tri-suction/V-cradle, failure replay, and promotion.
- **Figure 2:** v19-v25 timeline showing the single change, result, and diagnosis
  for each run.
- **Figure 3:** Expert velocity, VLA proposal, selected residual scale,
  Force-Memory cap, contact force, and task phase in one successful episode.
- **Table 1:** Software, Radeon/ROCm, training configuration, state/action
  dimensions, and hard gates.
- **Table 2:** The ablation matrix above.
- **Table 3:** Per-profile success, Wilson intervals, placement error, and force
  violations for the frozen 100-trial campaign.

## Classification and application boundary

The project has auditable routing based on shape, dimensions, mass, and handling
class. It maps parcels to carton, mailer, fragile, oversize, and cylindrical
destinations and injects the route into the language task. This is deterministic
semantic routing, not learned visual recognition of every parcel class. The
frozen VLA result covers small carton, flat mailer, electronics box, and medium
carton. The 21-profile catalog is a capability inventory, not 21 completed
handling claims.

## Threats and limitations

- PASH-v25 is one deterministic long-carton case, not a success rate or a
  significance result.
- The 96/100 campaign varies parameters within four known rigid profiles; it is
  not unseen-geometry generalization.
- Force Memory is Harness-side contact history, not a force token learned inside
  the foundation VLM.
- Self-improvement runs between episodes and never updates weights during an
  active rollout.
- There is no real-robot, deformable-parcel, learned visual-classification, or
  sim-to-real evidence yet.
- Single-Radeon training and inference are verified, but no upstream ROCm pull
  request has been completed.

## Minimum publication-integrity checklist

- Link every result to evidence JSON or a training log and SHA-256 digest.
- Retain v3, RGB-D, arm-residual, and v19/v21-v23 failures as negative evidence.
- Preserve the sources and Apache-2.0 notices for SmolVLA, SmolVLM2, LeRobot,
  Genesis, and Bi-Franka.
- Describe PASH-VLA as a system-level method, not a new foundation model or an
  undefined percentage of a state-of-the-art robot.
- Keep the README development-process and code-provenance sections consistent
  with the final source submission.
