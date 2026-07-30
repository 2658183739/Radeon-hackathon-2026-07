# Verified Harness Agent for Mobile Parcel Sorting

## Status and boundary

The Harness Agent protocol is implemented as a separate, nearline layer. It is
not part of the active 1,500-episode v8 collector and does not import into that
process. The current bulk collection must finish without changing its plan,
collector, output directory, policy checkpoint, or dataset writer.

The implementation establishes authority boundaries and evidence contracts. It
does not by itself establish an Agent performance gain. That claim requires a
frozen comparison after collection finishes.

## Control ownership

| Layer | Rate | May do | May not do |
| --- | ---: | --- | --- |
| Task Agent | 0.1-1 Hz | goals, task decomposition, grasp-mode intent, exception handling, memory lookup | joint, Cartesian, torque, tool, or safety commands |
| PI0.5 VLA executor | 3-10 Hz | base/arm action chunks and learned grasp execution | bypass Harness gates or activate weights |
| Deterministic servo | 240 Hz | interpolation, impedance, suction/tool execution | change the task or learn online |
| Safety Harness | every action | accept, project, reject, hold, or abort under fixed limits | create labels or optimize the model |
| Failure Analyst Agent | between episodes | diagnose failures and propose bounded corrections | execute proposals or label them positive |
| Independent Verifier | isolated replay | assess replay evidence | verify its own proposal |
| Promotion gate | between episodes | authorize an already evaluated artifact by hashes | infer actions or accept Agent assertions as evidence |

Agents never receive privileged simulator state. Fields such as parcel/object
pose, simulator state, contact points, raw actions, expert replacement actions,
safety overrides, or checkpoint activation requests are rejected at the
protocol boundary.

## Verified self-improvement path

1. A failed physical episode becomes a non-privileged failure packet.
2. The Failure Analyst proposes a high-level correction.
3. The proposal is hash-bound and marked `quarantined_unverified`; it is neither
   executable nor eligible for positive training.
4. A separately identified verifier evaluates a new physical replay.
5. Deterministic gates require full grasp, lift, transport, explicitly correct
   destination placement, release, non-empty RGB-D, every peak force below
   35 N, pure VLA attribution, no expert fallback or action replacement, and
   the v8 video/PyAV storage contract.
6. Only a verified successful correction receives the
   `verified_positive_correction` label. Failed actions remain negative
   telemetry and are never behavioral-cloning targets.
7. Training runs offline. A checkpoint still needs the existing paired frozen
   campaign, artifact hashes, safety gates, and the additional Agent provenance
   authorization before the active registry can change.

The checkpoint registry remains the only activation mechanism. Agents cannot
self-promote.

## Files

- `src/parcel_sorter/harness_agent.py`: identities, task directives, failure
  packets, correction quarantine, replay verification, training admission, and
  checkpoint authorization.
- `configs/mobile_harness_agent_v1.json`: declared identities, rates, and fixed
  storage/safety limits.
- `scripts/run_mobile_harness_agent_cycle.py`: non-executing cycle preparation
  and optional replay-evidence admission.
- `scripts/run_mobile_self_improvement_cycle_rocm.py`: accepts the optional
  `--harness-agent-cycle` evidence gate.
- `tests/test_harness_agent.py`: fail-closed authority and provenance tests.

## Usage after the bulk collector finishes

Prepare quarantined corrections from a campaign audit:

```bash
python scripts/run_mobile_harness_agent_cycle.py \
  --source-campaign-audit outputs/agent-development-audit.json \
  --config configs/mobile_harness_agent_v1.json \
  --output outputs/harness-agent-cycle-v1/cycle.json
```

No robot command is issued by that invocation. Corrections must be executed by
an isolated replay runner and written to a separate replay-audit JSON. A second
invocation with `--replay-audits` applies the deterministic admission gates.

For an Agent-derived training cycle, add the admitted record to the existing
self-improvement command:

```bash
python scripts/run_mobile_self_improvement_cycle_rocm.py \
  ... \
  --harness-agent-cycle outputs/harness-agent-cycle-v1/cycle-verified.json
```

If the Agent evidence is missing, modified, self-verified, assisted by an
expert, unsafe, incomplete, or stored outside the video contract, the candidate
remains quarantined even when its offline loss improves.

## Agent adapter

`TaskAgentAdapter` and `FailureAnalystAdapter` are provider-neutral. The task
adapter receives an allowlisted perception/task observation and can return only
a validated high-level directive. The repository includes a
deterministic taxonomy adapter for reproducible tests and dry runs. An external
LLM/Agent adapter must return the same structured analysis and declared model
identity; it receives the same non-privileged packet and gains no extra
authority. The independent verifier should use a different identity and should
not share hidden reasoning or mutable memory with the proposer.

## Required paper experiment

Use a frozen paired study with at least these arms:

| Arm | High-level planner | Action policy | Corrections admitted |
| --- | --- | --- | --- |
| PI0.5 baseline | fixed task program | PI0.5 | none |
| Harness only | fixed task program | PI0.5 + deterministic Harness | none |
| Harness Agent | Task/Failure Agents | same PI0.5 + same Harness | independently verified only |
| Assisted diagnostic | Agent + expert fallback | mixed | excluded from pure autonomous score |

Report overall and per-grasp-mode success, recovery success, intervention and
abort rates, force violations, completion time, Agent latency/cost, calibration
of verifier decisions, and promotion rejection rate. Freeze seeds and physical
parameter order before training. The defensible research claim is verified,
constraint-preserving self-improvement for a parcel-handling VLA, not generic
Agent control of a robot arm.
