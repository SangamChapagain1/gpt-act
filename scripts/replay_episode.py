import time
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.utils import log_say

from src.hardware.connect import make_robot

DATASET_ID = "sangam-101/so101-pick-and-place-carrot"
EPISODE_INDEX = 0

def replay_episode(dataset_id: str | None = None, episode_index: int | None = None) -> None:
    ds_id = dataset_id or DATASET_ID
    ep_idx = episode_index if episode_index is not None else EPISODE_INDEX

    robot = make_robot()
    robot.connect()
    try:
        dataset = LeRobotDataset(ds_id, episodes=[ep_idx])
        actions = dataset.hf_dataset.select_columns("action")
        log_say(f"Replaying episode {ep_idx}")
        for idx in range(dataset.num_frames):
            t0 = time.perf_counter()
            action = {
                name: float(actions[idx]["action"][i])
                for i, name in enumerate(dataset.features["action"]["names"])
            }
            robot.send_action(action)
            busy_wait(1.0 / dataset.fps - (time.perf_counter() - t0))
    finally:
        robot.disconnect()


if __name__ == "__main__":
    replay_episode()