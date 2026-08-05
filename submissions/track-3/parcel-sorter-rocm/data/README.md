# Data Contract

The submitted training evidence describes a local audited primitive dataset, not a public dataset release. Public dataset URL: **pending**.

| Field | Audited value |
| --- | --- |
| Episodes | 7 independent episodes |
| Frames | 4,557 |
| Rate | 30 fps |
| State | 43-D |
| Action | 20-D, including primitive progress |
| Policy image input | overhead RGB |
| Privileged state in policy input | false |
| RGB/depth audit | 65 checked frames; 0 mismatches |

The source audit is [`evidence/training/pash-primitive-dataset-v2-audit.json`](../evidence/training/pash-primitive-dataset-v2-audit.json). The recorded local dataset root is environment-specific and is not a portable download location. To recreate the derived dataset from a locally available LeRobot source dataset, use:

```bash
export PYTHONPATH="$PWD/src"
python3 scripts/build_mobile_primitive_dataset.py \
  --source /path/to/local/source-dataset \
  --output /path/to/local/mobile-primitive-dataset-v2
```

Do not treat expert/reference demonstrations as pure-VLA evaluation data.
