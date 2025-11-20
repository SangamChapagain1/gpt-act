from lerobot.utils.visualization_utils import init_rerun, log_rerun_data
from src.hardware.connect import connect_both, disconnect_both


def teleop_with_cameras() -> None:
    print("Connecting robots...")
    robot, teleop_device = connect_both()
    print(" Robots connected")

    print("Initializing Rerun viewer...")
    init_rerun(session_name="teleop_view")
    print(" Rerun initialized - check your browser!")
    print("\nMove the leader arm to control the follower.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            observation = robot.get_observation()
            action = teleop_device.get_action()
            robot.send_action(action)
            log_rerun_data(observation=observation, action=action)
    finally:
        disconnect_both(robot, teleop_device)
        print("\n Disconnected safely")


if __name__ == "__main__":
    teleop_with_cameras()