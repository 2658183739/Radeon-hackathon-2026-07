from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Any, Protocol

from .config import ExperimentConfig
from .contracts import CartesianAction, Observation, PolicyContext, RobotState, TrajectoryFrame
from .dataset import JsonlTrajectoryWriter, LeRobotTrajectoryWriter
from .expert import ScriptedPickPlaceExpert
from .metrics import EpisodeResult
from .policy import ActionPolicy, ScriptedExpertPolicy
from .randomization import ParcelSample
from .state_machine import ClosedLoopSupervisor, Stage


class ParcelEnvironment(Protocol):
    control_step: int

    def state(self) -> RobotState: ...
    def observation(self, state: RobotState | None = None) -> Observation: ...
    def step(self, action: CartesianAction) -> None: ...
    def sensor_frame(self) -> tuple[Any | None, Any | None]: ...
    def parcel_dropped(self) -> bool: ...


class FrameWriter(Protocol):
    def add_frame(self, frame: TrajectoryFrame) -> None: ...


@dataclass(frozen=True)
class EpisodeReport:
    episode_index: int
    result: EpisodeResult
    terminal_stage: str
    sample: ParcelSample
    trace: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_index": self.episode_index,
            "result": asdict(self.result),
            "terminal_stage": self.terminal_stage,
            "sample": self.sample.to_dict(),
            "trace": list(self.trace),
        }


def run_policy_episode(
    env: ParcelEnvironment,
    config: ExperimentConfig,
    sample: ParcelSample,
    episode_index: int,
    policy: ActionPolicy,
    writers: tuple[FrameWriter, ...] = (),
) -> EpisodeReport:
    supervisor = ClosedLoopSupervisor(
        config.task.max_grasp_retries,
        grasp_settle_steps=config.task.grasp_settle_steps,
        release_settle_steps=config.task.release_settle_steps,
    )
    trace: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    max_force = 0.0
    max_steps = int(config.task.episode_seconds * config.simulation.control_hz)

    for frame_index in range(max_steps):
        state = env.state()
        observation = env.observation(state)
        max_force = max(max_force, state.gripper_contact_force_n)
        rgb, depth = env.sensor_frame()
        started = time.perf_counter_ns()
        decision = supervisor.step(observation)
        action = policy.predict(
            PolicyContext(
                decision=decision,
                state=state,
                task=config.output.task_instruction,
                rgb=rgb,
                depth=depth,
            )
        )
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        frame = TrajectoryFrame(
            frame_index=frame_index,
            timestamp_seconds=frame_index / config.simulation.control_hz,
            stage=decision.stage,
            state=state,
            action=action,
            task=config.output.task_instruction,
            rgb=rgb,
            depth=depth,
        )
        for writer in writers:
            writer.add_frame(frame)
        trace.append(
            {
                "frame": frame_index,
                "stage": decision.stage,
                "command": decision.command,
                "reason": decision.reason,
                "retry_count": decision.retry_count,
            }
        )

        if supervisor.stage in {Stage.COMPLETE, Stage.ABORT}:
            break
        env.step(action)

    elapsed_sim = max((len(trace) - 1) / config.simulation.control_hz, 1 / config.simulation.control_hz)
    result = EpisodeResult(
        success=supervisor.stage == Stage.COMPLETE,
        retries=supervisor.retry_count,
        duration_seconds=elapsed_sim,
        inference_latency_ms=tuple(latencies_ms),
        dropped=env.parcel_dropped(),
        max_contact_force_n=max_force,
    )
    return EpisodeReport(
        episode_index=episode_index,
        result=result,
        terminal_stage=supervisor.stage.value,
        sample=sample,
        trace=tuple(trace),
    )


def run_expert_episode(
    env: ParcelEnvironment,
    config: ExperimentConfig,
    sample: ParcelSample,
    episode_index: int,
    writers: tuple[FrameWriter, ...] = (),
) -> EpisodeReport:
    policy = ScriptedExpertPolicy(ScriptedPickPlaceExpert(config, sample))
    return run_policy_episode(env, config, sample, episode_index, policy, writers)


def save_episode_writers(
    report: EpisodeReport,
    jsonl_writer: JsonlTrajectoryWriter | None,
    lerobot_writer: LeRobotTrajectoryWriter | None,
) -> None:
    if jsonl_writer is not None:
        jsonl_writer.save_episode(
            report.episode_index,
            {
                "success": report.result.success,
                "terminal_stage": report.terminal_stage,
                "retries": report.result.retries,
                "sample": report.sample.to_dict(),
            },
        )
    if lerobot_writer is not None:
        if report.result.success:
            lerobot_writer.save_episode()
        else:
            lerobot_writer.clear_episode()
