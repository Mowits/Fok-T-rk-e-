#!/usr/bin/env bash
set -euo pipefail

TEXT="${1:-}"
[ -z "$TEXT" ] && exit 0

PI_HOST="${FOK_PI_HOST:-192.168.1.111}"
PI_USER="${FOK_PI_USER:-mowits}"
PI_KEY="${FOK_PI_KEY:-/home/mowits/fok_pi_key}"

export FOK_TTS_TEXT="$TEXT"
export FOK_TTS_OPENAI_MODEL="${FOK_TTS_OPENAI_MODEL:-gpt-4o-mini-tts}"
export FOK_TTS_OPENAI_VOICE="${FOK_TTS_OPENAI_VOICE:-alloy}"
export FOK_TTS_OPENAI_FORMAT="${FOK_TTS_OPENAI_FORMAT:-wav}"

python3 - <<'PY' | ssh -i "$PI_KEY" -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" "paplay /dev/stdin 2>/dev/null || pw-play /dev/stdin 2>/dev/null || aplay -q -t wav - 2>/dev/null || aplay -D pulse -q -t wav - 2>/dev/null"
import os
import urllib.request

api_key = os.environ.get("OPENAI_API_KEY", "").strip()
if not api_key:
    raise SystemExit("OPENAI_API_KEY missing")

text = os.environ.get("FOK_TTS_TEXT", "").strip()
model = os.environ.get("FOK_TTS_OPENAI_MODEL", "gpt-4o-mini-tts")
voice = os.environ.get("FOK_TTS_OPENAI_VOICE", "alloy")
fmt = os.environ.get("FOK_TTS_OPENAI_FORMAT", "wav")

payload = {
    "model": model,
    "voice": voice,
    "format": fmt,
    "input": text,
}

req = urllib.request.Request(
    "https://api.openai.com/v1/audio/speech",
    data=bytes(__import__("json").dumps(payload), "utf-8"),
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
)

with urllib.request.urlopen(req, timeout=30) as resp:
    data = resp.read()
    os.write(1, data)
PY
