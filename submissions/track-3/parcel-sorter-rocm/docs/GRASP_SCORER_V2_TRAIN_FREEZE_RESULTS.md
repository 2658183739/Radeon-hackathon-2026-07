# Grasp Scorer V2: Train Freeze Results

## Outcome

On 2026-07-26, one AMD Radeon `gfx1100` completed the v2 train collection and
both capacity-matched model fits under ROCm 7.2. The train split contains 32
physical episode groups, eight from each of four profiles and six candidates
per group, for 192 closed-loop candidate executions. All 32 groups completed
without a collection failure. Neither development nor holdout existed before
the checkpoints were frozen.

Both formal models use 28 features, 6,276 parameters, 2,000 steps, learning
rate 0.001, weight decay 0.0001, and seed 42. Pointwise training took 2.872 s;
groupwise-safety-first took 46.162 s. Checkpoints, summaries, dataset, and
protocols are bound by SHA-256. The `device=cuda` value in PyTorch summaries is
the ROCm compatibility API name; the physical device is `AMD Radeon Graphics`
and the HIP version is `7.2.53211-e1a6bc5663`.

## Claim Boundary

On train, the static first choice produced 7/32 successes and 17/32 safety
aborts. Reconstructed pointwise selection produced 12/32 successes and 4/32
safety aborts; groupwise-safety-first produced 10/32 and 4/32. These numbers
only show that both objectives fit observed train groups. They cannot select a
model or support a generalization claim. Formal selection is restricted to the
one frozen 16-group development split; holdout remains locked.

Groupwise training is slower because it adds within-episode safety and success
pairs to the pointwise calibration terms. Training latency is not a promotion
metric. Deployment uses the preregistered warm six-candidate inference P95
threshold of less than 5 ms.

## Decisions and Rationale

1. Collect all 32 groups before fitting so partial train outcomes cannot alter
   later samples or hyperparameters.
2. Compare exactly two preregistered equal-capacity models so the objective,
   not model size or budget, is the controlled difference.
3. Let learning reorder only candidates that pass static IK and collision
   checks. Collision-checked reset, the 35 N abort, and the controller state
   machine remain independent.
4. Track only the freeze manifest, summaries, and compact index in Git. The
   226 MiB traces, dataset, and checkpoints remain in the Radeon workspace and
   are referenced by byte count and SHA-256.
5. Start development only after independent hash and AMD/HIP metadata checks
   pass. This order is enforced by code rather than an operator convention.

## Core Hashes

| Artifact | SHA-256 |
| --- | --- |
| Collection protocol | `1e9d644e68f0d2ead3d9f5012c6ec1de0c3e0d4da36150ef39f84431c7989f30` |
| Model-selection protocol | `091c8e28efcab4b59663e07b03ec51daa609d057fbff97a79b26adc9233241ee` |
| Train dataset file | `71761164467ba3b29866d87639b73474a5d5f2cc1fdb8907d62957a6c73703d5` |
| Pointwise checkpoint | `9e0945b57906f703b1cfa8764a4446eab3ecdf6958fca2e3d65f157a8c9952a5` |
| Groupwise checkpoint | `d2edbb9f66fe8279f303ea80e2bed46eb631232222ed357efd4fff372afce621` |

See `evidence/training/grasp-scorer-v2-train-evidence.json` for the
machine-readable record.

## Next Gate

Development must contain all 16 groups, four per profile. Both frozen models
are then evaluated on identical candidate groups. No profile may add a safety
abort, aggregate safety or task outcome must improve, and warm six-candidate
P95 must be below 5 ms. If neither model passes, the result is `no_promotion`:
development cannot be reused for tuning and holdout remains closed.
