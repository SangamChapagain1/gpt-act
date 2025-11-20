from src.hardware.connect import connect_both, disconnect_both


def teleop_no_camera() -> None:
    print("Connecting robots...")
    robot, teleop_device = connect_both()
    print(" Robots connected")

    print("\nMove the leader arm to control the follower (no camera UI).")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            action = teleop_device.get_action()
            robot.send_action(action)
    finally:
        disconnect_both(robot, teleop_device)
        print("\n Disconnected safely")

if __name__ == "__main__":
    teleop_no_camera()