import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.run_inference_pick_and_place import run_pick_and_place  # type: ignore


def policy_act_pick_and_place(
    model_id=None, num_episodes=None, episode_time_s=None, task_description=None
) -> str:
    try:
        kwargs = {}
        if model_id:
            kwargs["model_id"] = model_id
        if num_episodes is not None:
            kwargs["num_episodes"] = num_episodes
        if episode_time_s is not None:
            kwargs["episode_time_s"] = episode_time_s
        if task_description:
            kwargs["task_description"] = task_description
        run_pick_and_place(**kwargs)
        return "✓ COMPLETED: ACT pick-and-place finished."
    except Exception as e:
        return f"ERROR (ACT): {e}"


POLICY_FUNCTIONS = {
    "run_pick_and_place": policy_act_pick_and_place,
}