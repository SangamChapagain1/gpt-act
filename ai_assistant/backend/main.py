import asyncio
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import os
from pathlib import Path

from ai_assistant.backend.robot_policies import POLICY_FUNCTIONS
from ai_assistant.backend.camera_capture import capture_top_camera_image, release_camera
from ai_assistant.backend.vision_logger import save_image_and_analysis, save_master_log

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REALTIME_MODEL = "gpt-realtime-mini-2025-10-06"
VISION_MODEL = "gpt-4o"
OPENAI_API_BASE = "https://api.openai.com/v1"
DEMO_MODE = True  # Set to False if you want per-step confirmations instead of full demo mode

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:8080","http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global lock to prevent concurrent robot operations
policy_lock = asyncio.Lock()

class PolicyRequest(BaseModel):
    policy_name: str
    params: Dict[str, Any] = {}


@app.get("/")
def health():
    return {"status": "ok", "policies": list(POLICY_FUNCTIONS.keys())}


@app.get("/camera/capture")
async def capture_camera():
    try:
        image_base64 = capture_top_camera_image()
        return {"status": "success", "image": image_base64}
    except Exception as e:
        return {"status": "error", "message": f"Camera capture error: {e}"}


@app.post("/session")
async def create_realtime_session():
    tools = [
        {
            "type": "function",
            "name": "capture_scene",
            "description": "Capture an image from the top camera. Use skip_analysis=true for speed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skip_analysis": {
                        "type": "boolean",
                        "default": True,
                        "description": "If true, only capture and display; if false, also run GPT-4o analysis.",
                    }
                },
                "required": [],
            },
        },
        {
            "type": "function",
            "name": "run_pick_and_place",
            "description": "Run ACT carrot pick-and-place policy.",
            "parameters": {"type": "object", "properties": {}},
        },
    ]

    if DEMO_MODE:
        instructions = (
            "You control a single SO101 robot arm doing carrot pick-and-place.\n\n"
            "Workspace: baby carrots on a plate and cutting board in front of the robot.\n\n"
            "TOOLS:\n"
            "- capture_scene(skip_analysis=true): quickly grab a fresh camera image.\n"
            "- run_pick_and_place: use the ACT policy to move one carrot from plate to board.\n\n"
            "RULES:\n"
            "- Always ask the user for confirmation before calling run_pick_and_place.\n"
            "- When the policy is running, motors are active; wait around 25 seconds for completion before assuming the task is done.\n"
            "- After the function returns, call capture_scene(skip_analysis=true) to verify what happened, then describe it to the user.\n"
            "- Never move the robot directly; only call the ACT policy.\n"
        )
    else:
        instructions = (
            "You control a single SO101 arm for carrot pick-and-place.\n"
            "Ask before calling the ACT policy; wait for the function to complete (25 seconds) and then verify with capture_scene.\n"
        )

    session_config = {
        "session": {
            "type": "realtime",
            "model": REALTIME_MODEL,
            "audio": {"output": {"voice": "alloy"}},
            "instructions": instructions,
            "tools": tools,
        }
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{OPENAI_API_BASE}/realtime/client_secrets",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json=session_config,
        )
    if r.status_code != 200:
        return {"error": r.text, "status_code": r.status_code}
    data = r.json()
    return {"ephemeral_key": data.get("value", ""), "model": REALTIME_MODEL}

@app.post("/analyze_image")
async def analyze_image(request: Dict[str, Any]):
    try:
        image_base64 = request.get("image") or capture_top_camera_image()
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{OPENAI_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": VISION_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Describe the workspace and what should happen next."},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                                },
                            ],
                        }
                    ],
                    "max_tokens": 400,
                },
            )
        if r.status_code != 200:
            return {"status": "error", "message": r.text}
        description = r.json()["choices"][0]["message"]["content"]
        ts = save_image_and_analysis(image_base64, {"status": "success", "description": description})
        save_master_log(ts, {"description": description})
        return {"status": "success", "description": description, "timestamp": ts}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/robot/run_policy")
async def run_policy(req: PolicyRequest):
    func = POLICY_FUNCTIONS.get(req.policy_name)
    if not func:
        return {"status": "error", "message": f"Unknown policy {req.policy_name}"}

    # Acquire lock to prevent concurrent robot operations
    async with policy_lock:
        def _call():
            return func(**req.params)

        try:
            result = await asyncio.to_thread(_call)
            return {"status": "completed", "policy": req.policy_name, "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}


@app.on_event("shutdown")
async def shutdown_event():
    release_camera()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)