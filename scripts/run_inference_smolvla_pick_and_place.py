from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.policies.smolvla.processor_smolvla import make_smolvla_pre_post_processors
from lerobot.processor.factory import make_default_processors
from lerobot.processor import RenameObservationsProcessorStep
from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.utils.visualization_utils import init_rerun
from lerobot.utils.utils import log_say
from lerobot.scripts.lerobot_record import record_loop
from lerobot.datasets.pipeline_features import (
    aggregate_pipeline_dataset_features,
    create_initial_features,
)
from lerobot.datasets.utils import combine_feature_dicts

import sys
sys.path.insert(0, ".")
import time

from src.hardware.connect import connect_both
from src.config.ports_and_cameras import FPS

HF_MODEL_ID_DEFAULT = "sangam-101/smolvla_so101_pick_and_place_carrot"
TASK_DESCRIPTION_DEFAULT = "Pick carrot from plate and place on cutting board"
NUM_EPISODES_DEFAULT = 1
EPISODE_TIME_SEC_DEFAULT = 25

CAMERA_RENAME_MAP = {
    "observation.images.top": "observation.images.camera1",
    "observation.images.wrist": "observation.images.camera2",
}

def run_smolvla_pick_and_place(
    model_id: str | None = None,
    num_episodes: int | None = None,
    episode_time_s: int | float | None = None,
    task_description: str | None = None,
) -> None:
    hf_model_id = model_id or HF_MODEL_ID_DEFAULT
    task_description = task_description or TASK_DESCRIPTION_DEFAULT
    num_episodes = num_episodes if num_episodes is not None else NUM_EPISODES_DEFAULT
    episode_time_s = episode_time_s if episode_time_s is not None else EPISODE_TIME_SEC_DEFAULT

    print(f"Loading SmolVLA policy from {hf_model_id}...")
    policy = SmolVLAPolicy.from_pretrained(hf_model_id)
    print("✓ SmolVLA policy loaded!")

    print("Connecting robots...")
    robot, _ = connect_both()
    print("✓ Robots connected!")

    teleop_action_processor, robot_action_processor, robot_observation_processor = make_default_processors()

    dataset_features = combine_feature_dicts(
        aggregate_pipeline_dataset_features(
            pipeline=teleop_action_processor,
            initial_features=create_initial_features(action=robot.action_features),
            use_videos=True,
        ),
        aggregate_pipeline_dataset_features(
            pipeline=robot_observation_processor,
            initial_features=create_initial_features(observation=robot.observation_features),
            use_videos=True,
        ),
    )

    class _InferenceDataset:
        def __init__(self, features, fps):
            self.features = features
            self.image_writer = None
            self.fps = fps

        def add_frame(self, _frame):
            return

    inference_dataset = _InferenceDataset(dataset_features, FPS)

    print("Loading dataset statistics...")
    from lerobot.datasets.lerobot_dataset import LeRobotDataset

    training_dataset = LeRobotDataset("sangam-101/so101-pick-and-place-carrot")
    dataset_stats = training_dataset.meta.stats

    preprocessor, postprocessor = make_smolvla_pre_post_processors(
        config=policy.config,
        dataset_stats=dataset_stats,
    )
    preprocessor.steps.insert(0, RenameObservationsProcessorStep(rename_map=CAMERA_RENAME_MAP))
    for step in preprocessor.steps:
        if hasattr(step, "device"):
            step.device = "mps"

    _, events = init_keyboard_listener()
    init_rerun(session_name="inference_smolvla_pick_place")

    print("\n" + "=" * 60)
    print("SMOLVLA INFERENCE MODE - Robot controlled by VLA policy!")
    print("=" * 60)
    print(f"Task: {task_description}")
    print(f"Running {num_episodes} test episodes")

    try:
        for episode_idx in range(num_episodes):
            log_say(
                f"Running SmolVLA inference episode {episode_idx + 1} of {num_episodes}",
                play_sounds=False,
            )

            record_loop(
                robot=robot,
                events=events,
                fps=FPS,
                teleop_action_processor=teleop_action_processor,
                robot_action_processor=robot_action_processor,
                robot_observation_processor=robot_observation_processor,
                dataset=inference_dataset,
                policy=policy,
                preprocessor=preprocessor,
                postprocessor=postprocessor,
                control_time_s=episode_time_s,
                single_task=task_description,
                display_data=True,
            )

            if events["stop_recording"]:
                break

    finally:
        try:
            robot.send_action({"gripper.pos": 0})
            time.sleep(0.3)
        except Exception:
            pass
        try:
            robot.disconnect()
        except RuntimeError:
            try:
                robot.config.disable_torque_on_disconnect = False
                robot.disconnect()
            except Exception:
                pass
        print("✓ Disconnected safely")


if __name__ == "__main__":
    run_smolvla_pick_and_place()