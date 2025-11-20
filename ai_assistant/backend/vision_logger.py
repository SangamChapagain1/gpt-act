import json
from datetime import datetime
from pathlib import Path
import base64

LOGS_DIR = Path(__file__).parent.parent / "data" / "vision_logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def save_image_and_analysis(image_base64: str, analysis_result: dict) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    img_path = LOGS_DIR / f"image_{ts}.png"
    with open(img_path, "wb") as f:
        f.write(base64.b64decode(image_base64))
    json_path = LOGS_DIR / f"analysis_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(
            {
                "timestamp": ts,
                "datetime": datetime.now().isoformat(),
                "image_file": img_path.name,
                "analysis": analysis_result.get("description", ""),
                "status": analysis_result.get("status", ""),
                "model": "gpt-4o",
            },
            f,
            indent=2,
        )
    return ts

def save_master_log(timestamp: str, analysis_result: dict, policy_executed: str | None = None):
    master = LOGS_DIR / "master_log.jsonl"
    with open(master, "a") as f:
        f.write(
            json.dumps(
                {
                    "timestamp": timestamp,
                    "datetime": datetime.now().isoformat(),
                    "image_file": f"image_{timestamp}.png",
                    "analysis_file": f"analysis_{timestamp}.json",
                    "description_preview": (analysis_result.get("description", "") or "")[:100] + "...",
                    "policy_executed": policy_executed,
                }
            )
            + "\n"
        )