from pathlib import Path
import unittest

from parcel_sorter.config import load_config
from parcel_sorter.contracts import Observation, RobotState
from parcel_sorter.randomization import DomainRandomizer
from parcel_sorter.runner import run_expert_episode
from parcel_sorter.state_machine import Command


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeEnvironment:
    def __init__(self) -> None:
        self.control_step = 0
        self.observations = (
            Observation(parcel_visible=True),
            Observation(at_pregrasp=True),
            Observation(),
            Observation(grasp_contact=True),
            Observation(parcel_lifted=True),
            Observation(at_drop_pose=True, parcel_lifted=True),
            Observation(at_drop_pose=True, parcel_released=True),
        )

    def state(self) -> RobotState:
        return RobotState(
            joint_positions=(0.0,) * 9,
            end_effector_pose=(0.5, 0.0, 0.2, 1.0, 0.0, 0.0, 0.0),
            parcel_pose=(0.6, 0.0, 0.02, 1.0, 0.0, 0.0, 0.0),
            target_position=(0.48, -0.34, 0.025),
            gripper_contact_force_n=1.0,
        )

    def observation(self, state=None):
        return self.observations[self.control_step]

    def step(self, action):
        self.control_step += 1

    def sensor_frame(self):
        return None, None

    def parcel_dropped(self):
        return False


class ExpertRunnerTests(unittest.TestCase):
    def test_runs_complete_closed_loop(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        sample = DomainRandomizer(config.randomization, config.seed).sample(0)
        report = run_expert_episode(FakeEnvironment(), config, sample, 0)

        self.assertTrue(report.result.success)
        self.assertEqual(report.terminal_stage, "complete")
        self.assertIn(Command.MOVE_LIFT.value, [item["command"] for item in report.trace])


if __name__ == "__main__":
    unittest.main()
