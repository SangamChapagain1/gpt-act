import sys
from pathlib import Path
import base64
import cv2

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config.ports_and_cameras import camera_config

_top_camera = None

def initialize_top_camera():
    global _top_camera
    if _top_camera is not None:
        return
    if "top" not in camera_config:
        raise ValueError("Top camera not configured in ports_and_cameras.py")
    top = camera_config["top"]
    _top_camera = cv2.VideoCapture(top.index_or_path)
    if not _top_camera.isOpened():
        raise RuntimeError("Failed to open top camera")
    if hasattr(top, "width") and hasattr(top, "height"):
        _top_camera.set(cv2.CAP_PROP_FRAME_WIDTH, top.width)
        _top_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, top.height)


def capture_top_camera_image() -> str:
    global _top_camera
    if _top_camera is None:
        initialize_top_camera()
    ok, frame = _top_camera.read()
    if not ok or frame is None:
        raise RuntimeError("Failed to read from top camera")
    ok, buffer = cv2.imencode(".png", frame)  # BGR → PNG
    if not ok:
        raise RuntimeError("Failed to encode frame")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def release_camera():
    global _top_camera
    if _top_camera is not None:
        _top_camera.release()
        _top_camera = None