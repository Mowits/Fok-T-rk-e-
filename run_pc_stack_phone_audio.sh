#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3 phone_bridge_server.py &
PHONE_PID=$!

FOK_TTS_CMD="$(pwd)/tts_phone_bridge.sh" python3 "$(pwd)/fok_pi_agent.py" &
AGENT_PID=$!

cleanup() {
  kill "$AGENT_PID" >/dev/null 2>&1 || true
  kill "$PHONE_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

python3 main.py
