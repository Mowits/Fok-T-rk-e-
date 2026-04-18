#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"
export PYTHONUNBUFFERED=1

export FOK_CONFIG="${FOK_CONFIG:-$(pwd)/config_pi.json}"
export FOK_STT_ENGINE="${FOK_STT_ENGINE:-openai}"
export FOK_STT_OPENAI_MODEL="${FOK_STT_OPENAI_MODEL:-gpt-4o-transcribe}"
export FOK_STT_LANGUAGE="${FOK_STT_LANGUAGE:-tr}"
export FOK_STT_PAUSE_LMSTUDIO=0
export FOK_PC_HOST="127.0.0.1"
export FOK_PC_AUDIO_PORT="${FOK_PC_AUDIO_PORT:-8767}"
export FOK_PI_SOURCE="${FOK_PI_SOURCE:-pulse}"
export FOK_PI_SOURCE_MODE="${FOK_PI_SOURCE_MODE:-auto}"

LOG_DIR="/tmp"
STT_LOG="$LOG_DIR/fok_pi_stt.log"
MIC_LOG="$LOG_DIR/fok_pi_mic_stream.log"
MAIN_LOG="$LOG_DIR/fok_pi_main.log"

pkill -f 'fok_pc_whisper_stt.py|run_pi_mic_stream.sh|main.py|fok_pi_agent.py' >/dev/null 2>&1 || true

# Local TTS -> local speaker (OpenAI)
FOK_TTS_CMD="$(pwd)/tts_openai_local.sh" \
stdbuf -oL -eL python3 "$(pwd)/fok_pi_agent.py" >"$LOG_DIR/fok_pi_agent.log" 2>&1 &
AGENT_PID=$!

cleanup() {
  kill "$AGENT_PID" >/dev/null 2>&1 || true
  pkill -f 'fok_pc_whisper_stt.py|run_pi_mic_stream.sh|main.py' >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

# STT server (OpenAI transcribe)
nohup stdbuf -oL -eL python3 fok_pc_whisper_stt.py >"$STT_LOG" 2>&1 &
sleep 1

# Mic stream -> local STT server
nohup stdbuf -oL -eL bash run_pi_mic_stream.sh >"$MIC_LOG" 2>&1 &
sleep 1

# Main app
stdbuf -oL -eL python3 main.py | tee "$MAIN_LOG"
