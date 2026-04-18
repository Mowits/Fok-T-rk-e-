#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Bu stack: STT PC whisper, TTS PC piper, hoparlor Pi.
# Gerekenler:
# - PC: piper + model
# - Pi: aplay + ssh erisimi

export FOK_PI_HOST="${FOK_PI_HOST:-192.168.1.111}"
export FOK_PI_USER="${FOK_PI_USER:-mowits}"
export FOK_PI_KEY="${FOK_PI_KEY:-/home/mowits/fok_pi_key}"
export FOK_SD_OPEN_TARGET="${FOK_SD_OPEN_TARGET:-pi}"
export FOK_SD_PAUSE_LMSTUDIO="${FOK_SD_PAUSE_LMSTUDIO:-1}"
export FOK_LMSTUDIO_RESTART_CMD="${FOK_LMSTUDIO_RESTART_CMD:-lm-studio}"

python3 "$(pwd)/fok_text_box.py" >/tmp/fok_text_box.log 2>&1 &
TEXTBOX_PID=$!

# Local agent (PC) TTS komutunu Pi hoparlore stream eder.
# FOK_MAX_TTS_CHARS=0: metni kesmeden tam oku.
TTS_ENGINE="${FOK_TTS_ENGINE:-openai}"
if [ "$TTS_ENGINE" = "openai" ]; then
  TTS_CMD="$(pwd)/tts_openai_to_pi.sh"
else
  TTS_CMD="$(pwd)/tts_piper_to_pi.sh"
fi

FOK_MAX_TTS_CHARS="${FOK_MAX_TTS_CHARS:-0}" \
FOK_TTS_CMD="$TTS_CMD" \
python3 "$(pwd)/fok_pi_agent.py" &
AGENT_PID=$!

cleanup() {
  kill "$TEXTBOX_PID" >/dev/null 2>&1 || true
  kill "$AGENT_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

python3 main.py
