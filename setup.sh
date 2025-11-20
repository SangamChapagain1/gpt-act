#!/bin/bash
# Usage: source setup.sh
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -f "../robotics_env/bin/activate" ]; then
  source ../robotics_env/bin/activate
else
  echo "Virtual env ../robotics_env not found. Create and install requirements:"
  echo "  python -m venv ../robotics_env && source ../robotics_env/bin/activate"
  echo "  pip install -r requirements.txt"
fi

export PYTHONPATH=.
if [ -f ".env" ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi
echo "Environment ready. PYTHONPATH=. ; OPENAI_API_KEY=${OPENAI_API_KEY:+set}"