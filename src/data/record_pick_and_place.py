from pathlib import Path
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.video_utils import VideoEncodingManager
from lerobot.datasets.pipeline_features import (
    aggregate_pipeline_dataset_features,
    create_initial_features,
)
from lerobot.datasets.utils import combine_feature_dicts
from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.utils.visualization_utils import init_rerun
from lerobot.utils.utils import log_say
from lerobot.scripts.lerobot_record import record_loop
from lerobot.processor.factory import (
    make_default_teleop_action_processor,
    make_default_robot_action_processor,
    make_default_robot_observation_processor,
)

from ..hardware.connect import connect_both, disconnect_both
from ..config.ports_and_cameras import FPS

REPO_ID = "sangam-101/so101-pick-and-place-carrot"
TASK_DESCRIPTION = "Pick carrot from plate and place on cutting board"
NUM_EPISODES = 80
EPISODE_TIME_SEC = 25
RESET_TIME_SEC = 10

robot, teleop_device = connect_both()

# Check if dataset exists locally (resume mode)
cache_dir = Path.home() / ".cache" / "huggingface" / "lerobot" / REPO_ID.replace("/", "/")
dataset_exists = cache_dir.exists()

# Create default processors (no modification to actions/observations)
teleop_action_processor = make_default_teleop_action_processor()
robot_action_processor = make_default_robot_action_processor()
robot_observation_processor = make_default_robot_observation_processor()

# Build dataset feature spec using the same pipeline logic as official CLI
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

if dataset_exists:
    print(f"Found existing dataset at {cache_dir}")
    print("Resuming recording...")
    dataset = LeRobotDataset(REPO_ID)
    if hasattr(robot, "cameras") and len(robot.cameras) > 0:
        dataset.start_image_writer(
            num_processes=0,
            num_threads=4 * len(robot.cameras),
        )
    starting_episode = dataset.num_episodes
    print(f"Loaded {starting_episode} existing episodes")
    print(f"Will record {NUM_EPISODES - starting_episode} more episodes (target: {NUM_EPISODES} total)\n")
else:
    print(f"Creating new dataset: {REPO_ID}")
    dataset = LeRobotDataset.create(
        repo_id=REPO_ID,
        fps=FPS,
        features=dataset_features,
        robot_type=robot.name,
        use_videos=True,
        image_writer_threads=4,
    )
    starting_episode = 0
    print(f"New dataset created")
    print(f"Will record {NUM_EPISODES} episodes\n")

_, events = init_keyboard_listener()
init_rerun(session_name="record_pick_place")

print("="*60)
print("RECORDING INSTRUCTIONS")
print("="*60)
print(f"Dataset: {REPO_ID}")
print(f"Task: {TASK_DESCRIPTION}")
if dataset_exists:
    print(f"Resuming from episode {starting_episode + 1}")
    print(f"Target episodes: {NUM_EPISODES} total ({NUM_EPISODES - starting_episode} more to record)")
else:
    print(f"Target episodes: {NUM_EPISODES} (new dataset)")
print(f"Episode time: {EPISODE_TIME_SEC}s, Reset time: {RESET_TIME_SEC}s")
print("\nCONTROLS:")
print("  → (Right Arrow): Skip to next phase (use carefully!)")
print("  ← (Left Arrow):  Re-record current episode")
print("  ESC:             Stop and upload")
print("\n IMPORTANT: Let each recording phase complete naturally!")
print("   Only press → if you need to skip. Otherwise, wait for voice cues.")
print("="*60 + "\n")

try:
    # Wrap recording loop with VideoEncodingManager (ensures videos are properly encoded before upload)
    with VideoEncodingManager(dataset):
        try:
            episode_idx = starting_episode
            while episode_idx < NUM_EPISODES and not events["stop_recording"]:
                # Announce episode (matching official LeRobot behavior at line 451 of lerobot_record.py)
                log_say(f"Recording episode {dataset.num_episodes}", play_sounds=True)

                record_loop(
                    robot=robot,
                    events=events,
                    fps=FPS,
                    teleop_action_processor=teleop_action_processor,
                    robot_action_processor=robot_action_processor,
                    robot_observation_processor=robot_observation_processor,
                    teleop=teleop_device,
                    dataset=dataset,
                    control_time_s=EPISODE_TIME_SEC,
                    single_task=TASK_DESCRIPTION,
                    display_data=True,
                )

                if not events["stop_recording"] and (
                    episode_idx < NUM_EPISODES - 1 or events["rerecord_episode"]
                ):
                    log_say("Reset the environment", play_sounds=True)
                    record_loop(
                        robot=robot,
                        events=events,
                        fps=FPS,
                        teleop_action_processor=teleop_action_processor,
                        robot_action_processor=robot_action_processor,
                        robot_observation_processor=robot_observation_processor,
                        teleop=teleop_device,
                        control_time_s=RESET_TIME_SEC,
                        single_task=TASK_DESCRIPTION,
                        display_data=True,
                    )

                if events["rerecord_episode"]:
                    log_say("Re-record episode", play_sounds=True)
                    events["rerecord_episode"] = False
                    events["exit_early"] = False
                    dataset.clear_episode_buffer()
                    continue

                # Only save if we actually recorded frames (not skipped with right arrow)
                if len(dataset.episode_buffer["action"]) > 0:
                    dataset.save_episode()
                    episode_idx += 1
                else:
                    log_say("Episode skipped - no frames recorded", play_sounds=True)
                    dataset.clear_episode_buffer()

            # Announce stop (matching official LeRobot behavior at line 498 of lerobot_record.py)
            log_say("Stop recording", play_sounds=True, blocking=True)
        except KeyboardInterrupt:
            log_say("Stop recording", play_sounds=True, blocking=True)
finally:
    # Ensure robot and teleop get disconnected even if encoding/upload fails
    disconnect_both(robot, teleop_device)

# Videos are now properly encoded after exiting VideoEncodingManager context,
# so it is safe to push to the Hub.
if dataset.num_episodes > 0:
    dataset.push_to_hub()
    print(f"\n✓ Upload complete! View at: https://huggingface.co/datasets/{REPO_ID}")
    if dataset_exists:
        print(f"✓ Total episodes in dataset: {dataset.num_episodes} (added {dataset.num_episodes - starting_episode} new)")
    else:
        print(f"✓ Total episodes recorded: {dataset.num_episodes}")
else:
    print("\nNo episodes recorded. Skipping upload.")

# Final announcement (matching official LeRobot behavior at line 510 of lerobot_record.py)
log_say("Exiting", play_sounds=True)