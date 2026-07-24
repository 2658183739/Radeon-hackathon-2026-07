# Multimodal Evidence

These artifacts distinguish the invalid historical depth scale from the
corrected RGB-D pipeline.

| Artifact | Meaning |
| --- | --- |
| `old-dataset-rgb-audit.json` | Old 96-episode shard remains usable for RGB, with a depth warning |
| `old-dataset-rgbd-audit.json` | Expected hard rejection for RGB-D |
| `corrected-dataset-audit.json` | One-episode corrected shard passes RGB-D metadata checks |
| `corrected-expert-summary.json` | Sensor-chain collection smoke on Radeon |
| `act-rgbd-smoke-config.json` | Saved ACT checkpoint requests RGB plus depth-view inputs |
| `act-rgbd-closed-loop-summary.json` | One-update checkpoint load/inference smoke; not a capability result |

The corrected sensor shard contained 152 frames with raw metric depth from
0.737 to 3.535 m and median 1.164 m. The ACT smoke completed one optimization
step with 51,577,736 parameters. Its one closed-loop episode failed, as expected
for a one-update model; the artifact proves only the input and runtime path.

## SHA-256

```text
E53F007C23C6166835E44955518D2F9CBEBEB6EAB933D4D112C05ED8A032D5B6  act-rgbd-closed-loop-summary.json
A8F6872563C308C4E5B9276466865810F966402692BD2DA49579A08AF26FEEB6  act-rgbd-smoke-config.json
484FDAE1F20E97B37CF452009EE57D02AE048ED6E2BB2EE720961F0CD758D3C4  corrected-dataset-audit.json
F9A80A342C97E4209C84DB6FC30C0E6621E5E524FEA70323E50D56A6A53C945C  corrected-expert-summary.json
9A240E81C4AC3CB3D9D1950DDCF2DB164E68EA18F9ED5FFAA83E992CC6EEDFAE  old-dataset-rgb-audit.json
CFAA7BF102302AD182649C2C06616254E56E555EB13BA9A3BE9764BC525D02E8  old-dataset-rgbd-audit.json
```
