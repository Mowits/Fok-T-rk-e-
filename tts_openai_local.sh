#!/usr/bin/env bash
set -euo pipefail

TEXT="${1:-}"
[ -z "$TEXT" ] && exit 0

export FOK_TTS_TEXT="$TEXT"
export FOK_TTS_OPENAI_MODEL="${FOK_TTS_OPENAI_MODEL:-gpt-4o-mini-tts}"
export FOK_TTS_OPENAI_VOICE="${FOK_TTS_OPENAI_VOICE:-alloy}"
export FOK_TTS_OPENAI_FORMAT="${FOK_TTS_OPENAI_FORMAT:-wav}"

python3 - <<'PY' | (aplay -q -t wav - 2>/dev/null || aplay -D pulse -q -t wav - 2>/dev/null || paplay - 2>/dev/null)
import os
import urllib.request
import json

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
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
)

with urllib.request.urlopen(req, timeout=30) as resp:
    data = resp.read()
    os.write(1, data)
PY
