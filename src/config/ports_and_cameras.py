from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

# Update these to match your machine
FOLLOWER_PORT = "/dev/tty.usbmodem58370529381"
LEADER_PORT   = "/dev/tty.usbmodem5A460815221"

camera_config = {
    "top":   OpenCVCameraConfig(index_or_path=0, width=1920, height=1080, fps=30),
    "wrist": OpenCVCameraConfig(index_or_path=1, width=1920, height=1080, fps=30),
}

FPS = 30
ROBOT_ID  = "follower_arm_2"
LEADER_ID = "leader_arm_2"