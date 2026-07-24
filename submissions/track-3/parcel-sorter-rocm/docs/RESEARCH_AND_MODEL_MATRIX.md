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

Warnings: citation counts and repository activity are time-dependent. GitHub
license metadata describes the repository, not all weights or dependencies.
No candidate is considered ROCm-compatible until it executes on the target
Radeon and produces a retained log.
