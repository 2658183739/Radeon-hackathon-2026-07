# Demonstration Video / 演示视频

- [59-second 1080p MP4 / 59 秒 1080p 成片](genesis_panda_8_success_reference_demo.mp4)
- [5-second hook GIF / 5 秒预览](../docs/assets/hook_5_seconds.gif)
- [Decode and source audit / 解码与来源审计](video_metadata_decode.json)
- [Reproducible render script / 可复现剪辑脚本](build_demo_video.py)

The video contains only the eight successful episodes selected from the
10-episode deterministic scripted expert-agent development screen: `0, 1, 2, 4,
6, 7, 8, 9`. Episodes 0 and 7 include synchronized overview and wrist views.
The other six use the overview view. The final render is 1920x1080 H.264,
59.0 seconds, with burned-in Chinese and English captions. Its source
simulation streams are 224x224 and are not described as native 1080p.

视频只包含 10 回合确定性脚本专家 agent 开发筛选中的 8 个成功回合：`0、1、2、4、
6、7、8、9`。回合 0 和 7 同时展示同步全景与腕部视角，其余六个回合展示全景。
最终成片为 1920x1080 H.264、59.0 秒，并烧录中英双语字幕。仿真源视频为
224x224，不宣称为原生 1080p。

This is scripted-agent simulation evidence, not real-robot footage and not a
pure-VLA result. The agent reads privileged simulator state. The strict pure-VLA campaign remains 0/3. A Bilibili/YouTube
URL requires an authenticated publisher account and is pending; the small
3.6 MB repository copy remains directly reviewable in the meantime.

这是使用仿真特权状态的脚本专家 agent 证据，不是真实机器人视频，也不是纯 VLA 成绩。严格纯 VLA 结果仍为
0/3。Bilibili/YouTube 地址需要已登录的发布账号，目前待补；仓库内约 3.6 MB 的
视频副本可供评审直接查看。

To rebuild the composite after reproducing the source recordings:

```bash
python3 videos/build_demo_video.py \
  --source-root /path/to/success-video-pack/expert \
  --two-view-root /path/to/expert-two-view \
  --font /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
  --out /tmp/parcel-sorter-demo
```
