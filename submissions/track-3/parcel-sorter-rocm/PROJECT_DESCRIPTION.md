# Project Description

Parcel Sorter ROCm runs a Franka Panda parcel-sorting task in Genesis on one
AMD Radeon GPU. A parcel appears at a randomized pose and must be placed in the
requested bin. The recorded setup uses ROCm 7.2.1, Genesis 1.2.3, and a
Radeon `gfx1100` device.

The visible result is deliberately straightforward: the 45.6-second demo joins
eight successful fixed-seed runs from a ten-episode screen. They were produced
by `ScriptedPickPlaceExpert + ClosedLoopSupervisor`, which reads privileged
simulator state. The video is a demonstration of the scripted workcell, not a
learned-policy or real-robot result.

The learned-policy work is reported separately. SmolVLA and PI0.5 actions pass
through bounded Cartesian, force, IK, and tool-command checks. Raw VLA passed
0/42 offline action-envelope checks; safety-clipped VLA and Harness-Lite passed
42/42. The strict pure-VLA closed-loop test scored 0/3. Those numbers are kept
separate because they answer different questions.

The main engineering lesson was that close-looking actions are not necessarily
executable actions. A learned command could be numerically near the expert yet
violate the motion contract. Keeping that failure visible led to the safety
checks and to controller-specific result records.

The submitted SmolVLA checkpoint records a 7-episode, 4,557-frame training set,
but that original binary payload is no longer present on the Radeon workspace.
The local delivery includes a separate seven-episode successful-trajectory
dataset and does not attribute it to that checkpoint. GPT-5.6 Luna/Codex Runtime
was used as a development tool; it is not a robot runtime controller.
