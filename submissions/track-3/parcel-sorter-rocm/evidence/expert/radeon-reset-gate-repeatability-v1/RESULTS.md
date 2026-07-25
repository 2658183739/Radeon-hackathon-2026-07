# Reset-Gate Execution Repeatability Results

## Design boundary

This study repeated the four success-discordant validation episodes five times
under each condition. The four unique randomized episodes are the experimental
units; the 40 executions are nested technical repeats and must not be reported
as 40 independent task samples. A seeded blocked schedule (`20260725`) balanced
which condition ran first across all 20 blocks: 10 baseline-first and 10
candidate-first.

The execution schedule alternated conditions within one Python/Genesis process
to reuse compiled Radeon kernels. Every observation still built and closed a
new physical scene. This measures within-process scene repeatability and exposes
period/carry-over effects; it does not replace fresh-process replication.

## Episode-level result

| Episode | Planner state | Baseline success | Candidate success | Interpretation |
| --- | --- | ---: | ---: | --- |
| `4120001 medium_carton` | active in candidate 5/5 | 5/5 | 0/5 | planner regression repeated |
| `5120000 shoe_box_proxy` | inactive in candidate 5/5 | 2/5 | 2/5 | scene-order instability, not planner effect |
| `5120003 shoe_box_proxy` | active in candidate 5/5 | 0/5 | 5/5 | planner recovery repeated |
| `7120004 large_narrow_carton` | active in candidate 5/5 | 5/5 | 0/5 | planner regression repeated |

The three planner-active episodes were exactly stable across all five repeats.
Their peak-force ranges also collapsed to the same recorded values within each
condition: 5.37 N versus 159.27 N for `4120001`, 42.24 N versus 29.69 N for
`5120003`, and 15.61 N versus 69.00 N for `7120004`. Under this execution
regime, the active planner therefore has one reproducible recovery and two
reproducible safety regressions.

`5120000` never activated the planner. Baseline succeeded 0/3 times when run
first in a block and 2/2 when run second. The gated condition succeeded 0/2
when first and 2/3 when second. All four successes occurred in the second
position. This is evidence of a process-local period or carry-over effect, not
evidence that the inactive planner changed the policy. A fresh-process study
would be required to separate kernel/process initialization from scene-order
state.

## Decision

The repeatability evidence strengthens the rejection of reset-risk-gated
planning. Its active intervention reproducibly regressed two of three changed
episodes, while the only inactive change is explained by an observed order
effect. The method remains default-off and the confirmation namespace remains
sealed.

The simulator reliability issue becomes an explicit project result: matched
episode IDs and deterministic seeds are necessary but not sufficient evidence
of identical closed-loop execution. Future comparisons must record process
boundaries and run position, balance order within episode/profile blocks, and
use fresh-process repeats for selected sentinels before causal promotion.

## Artifacts

- `schedule.json`: exact seeded block and condition order.
- `execution-events.jsonl`: one structured record per execution.
- `repeatability-analysis.json`: nested episode/condition sequences and
  position summaries.
- `REMOTE-SUMMARY-SHA256SUMS`: hashes for all 40 trace-rich summaries retained
  on the Radeon host.
- `SHA256SUMS`: verified hashes for all locally archived compact artifacts.
- `RUN-METADATA.txt` and `SOURCE-SHA256SUMS`: hardware, design, commit, and
  reporting provenance.
