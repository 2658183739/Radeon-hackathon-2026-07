# Catalog Evidence

`catalog-v1-submit-smoke.json` is copied from the final 20-second catalog
smoke on the verified Radeon instance after the local `configs/catalog_v1.toml`
was synchronized.

| Field | Value |
| --- | --- |
| Command | `python scripts/evaluate_catalog.py --backend rocm --episodes-per-profile 1` |
| GPU | AMD Radeon Graphics, `gfx1100` |
| VRAM | 47.98 GiB |
| ROCm | 7.2.1 / HIP runtime |
| Genesis | 1.2.3, `gs.amdgpu` |
| Config | `configs/catalog_v1.toml`, 20 s episodes |
| SHA-256 | `7b69a332faea59f6e930acfec653ec118f858c6002cd9d78d20a06bd8f142be0` |

The file contains one deterministic episode for each of the seven training
profiles. It is a regression smoke, not a statistically valid success-rate
claim. Four box profiles completed; the micro box and two cylinder profiles
remain explicit hard cases.
