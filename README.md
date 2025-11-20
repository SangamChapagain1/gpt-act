# GPT‑ACT (Carrot Pick-and-Place Demo)
Minimal repo showing an AI voice assistant controlling an ACT policy on the SO101 for carrot pick and place.

## Overview
## Demo videos
- **Short demo (2 min)**: [Autonomous Carrot Slicer Robot using GPT ACT VLA System](https://youtu.be/2TAfNOfgM9k)
- **Full run (8.5 min)**: [GPT ACT on an autonomous carrot slicer robot (8 min demo)](https://youtu.be/ARiFkiiq41E)

This repo shows a minimal end-to-end setup where GPT controls a single ACT pick-and-place policy on an SO-101 arm.
The assistant talks to you over voice and calls one policy function to move a carrot from the plate to the cutting board.

![Robot setup](assets/Carrot_Slicer_Robot_Setup.png)
![Top camera view](assets/Top_Camera_View.png)

## Before you start
- **Have SO-101 + LeRobot working first**: follow the official LeRobot docs to assemble, wire, and teleoperate the arm.
- **Be comfortable with Python and the terminal**: creating a virtualenv, running `git clone`, `pip install`, and Python scripts.
- **Verify basic LeRobot scripts**: make sure you can teleop and record with SO-101 from the LeRobot repo before using this assistant.

## Quick Start
1) Create or activate the shared `robotics_env` virtual environment
```bash
cd /path/to/your/projects_root
python -m venv robotics_env
source robotics_env/bin/activate
```
Place `lerobot/` and `gpt-act/` as siblings under this folder so the layout looks like:
```bash
projects_root/
  lerobot/
  gpt-act/
  robotics_env/
```
If you keep `lerobot` somewhere else, that is fine too — just make sure you install it into the **same** `robotics_env` you activate above.

2) Install dependencies into `robotics_env`
```bash
cd lerobot
pip install -e .

cd ../gpt-act
pip install -r requirements.txt
```

3) Run the carrot pick and place voice assistant (SO101)
```bash
cd gpt-act
source ./setup.sh
./start_ai_assistant.sh
```
Open `http://localhost:8080`, click “Connect and Start”, and say “pick up the carrot and place it on the cutting board”.

4) Record your own dataset
```bash
cd gpt-act
source ./setup.sh
python src/data/record_pick_and_place.py
```
This will record 80 episodes to `sangam-101/so101-pick-and-place-carrot` on HuggingFace. Adjust the repo ID and episode count inside the script.

5) Train ACT policy on Google Colab
See `colab_training_examples/train_act_pick_and_place.ipynb` for a ready-to-use notebook (~1.5h on A100). Upload it to [Google Colab](https://colab.research.google.com/), update the dataset/model IDs, and run all cells.

Optional: `train_smolvla_pick_and_place.ipynb` is also included for reference, but the voice assistant only calls the ACT policy.

6) Other useful scripts
- `scripts/run_inference_pick_and_place.py` – run ACT policy directly (without voice).
- `scripts/teleop_with_cameras.py` – leader–follower teleop with Rerun viewer.
- `scripts/teleop_no_camera.py` – leader–follower teleop without viewer.
- `scripts/replay_episode.py` – replay a recorded pick-and-place episode.

Note: `scripts/run_inference_smolvla_pick_and_place.py` exists for reference but is not used by the voice assistant.

## Community
- Discord: [Join the GPT-ACT robotics Discord](https://discord.gg/JEJPc5V4Kj)


## Python environment notes
- Both `lerobot` and this repo are installed into the same virtualenv (`robotics_env`).
- `setup.sh` assumes the env lives one level up as `../robotics_env`. If your layout is different, either move the env or update that path in `setup.sh`.
- All Python packages (OpenAI, FastAPI, httpx, etc.) are installed into `robotics_env` via `requirements.txt`, so your system Python stays clean.

## License
Apache‑2.0
## Architecture (in short)
- **Planner**: GPT Realtime (vision + language + function calls)
- **Executor**: Single ACT pick-and-place policy trained with LeRobot
- **Boundary**: GPT decides *when* to run the skill; ACT handles low-level control; camera verifies after each run.

## Extending this repo
This repo is intentionally minimal. If you want to extend it:
- Add new ACT policies (e.g., placing to different locations) and expose them via `ai_assistant/backend/robot_policies.py`.
- Update the instructions in `ai_assistant/backend/main.py` to teach GPT how and when to call new skills.
- Keep the separation clear: GPT plans at a high level; ACT policies stay focused on reliable low-level control.

