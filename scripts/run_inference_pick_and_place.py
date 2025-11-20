from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors
from lerobot.processor.factory import make_default_processors
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

HF_MODEL_ID_DEFAULT = "sangam-101/act_so101_pick_and_place_carrot_policy"
TASK_DESCRIPTION_DEFAULT = "Pick carrot from plate and place on cutting board"
NUM_EPISODES_DEFAULT = 1
EPISODE_TIME_SEC_DEFAULT = 25


def run_pick_and_place(
    model_id: str | None = None,
    num_episodes: int | None = None,
    episode_time_s: int | float | None = None,
    task_description: str | None = None,
) -> None:
    hf_model_id = model_id or HF_MODEL_ID_DEFAULT
    task_description = task_description or TASK_DESCRIPTION_DEFAULT
    num_episodes = num_episodes if num_episodes is not None else NUM_EPISODES_DEFAULT
    episode_time_s = episode_time_s if episode_time_s is not None else EPISODE_TIME_SEC_DEFAULT

    print(f"Loading policy from {hf_model_id}...")
    policy = ACTPolicy.from_pretrained(hf_model_id)
    print("✓ Policy loaded!")

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

    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy,
        pretrained_path=hf_model_id,
        dataset_stats=None,
        preprocessor_overrides={"device_processor": {"device": "mps"}},
    )

    _, events = init_keyboard_listener()
    init_rerun(session_name="inference_pick_place")

    print("\n" + "=" * 60)
    print("INFERENCE MODE - Robot is now controlled by ACT policy!")
    print("=" * 60)
    print(f"Task: {task_description}")
    print(f"Running {num_episodes} test episodes")
    print("\nControls:")
    print("  ESC: Stop inference")
    print("=" * 60 + "\n")

    try:
        for episode_idx in range(num_episodes):
            log_say(
                f"Running inference episode {episode_idx + 1} of {num_episodes}",
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

            if episode_idx < num_episodes - 1:
                log_say("Reset the environment for next test", play_sounds=False)
                input("Press Enter when ready for next episode...")

        log_say("Inference complete", play_sounds=False)
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
    run_pick_and_place()