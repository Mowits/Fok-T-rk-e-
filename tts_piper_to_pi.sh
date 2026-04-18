#!/usr/bin/env bash
set -euo pipefail
TEXT="${1:-}"
[ -z "$TEXT" ] && exit 0
MODEL="${FOK_PC_PIPER_MODEL:-$HOME/piper_pc/tr_TR-dfki-medium.onnx}"
PI_HOST="${FOK_PI_HOST:-192.168.1.111}"
PI_USER="${FOK_PI_USER:-mowits}"
PI_KEY="${FOK_PI_KEY:-/home/mowits/fok_pi_key}"
PIPER_BIN="${FOK_PC_PIPER_BIN:-$HOME/piper_bin/piper/piper}"

if [ ! -x "$PIPER_BIN" ]; then
  echo "[TTS-PC] piper bin yok: $PIPER_BIN" >&2
  exit 1
fi
if [ ! -f "$MODEL" ]; then
  echo "[TTS-PC] model yok: $MODEL" >&2
  exit 1
fi

echo "$TEXT" | "$PIPER_BIN" --model "$MODEL" --output-raw | ssh -i "$PI_KEY" -o StrictHostKeyChecking=no "$PI_USER@$PI_HOST" "paplay --raw --rate=22050 --channels=1 --format=s16le - 2>/dev/null || pw-play --rate 22050 --channels 1 --format s16 - 2>/dev/null || aplay -D pulse -q -r 22050 -f S16_LE -t raw 2>/dev/null"
