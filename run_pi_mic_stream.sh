#!/usr/bin/env bash
set -euo pipefail

PC_HOST="${FOK_PC_HOST:-192.168.1.111}"
PC_PORT="${FOK_PC_AUDIO_PORT:-8767}"
SOURCE_MODE="${FOK_PI_SOURCE_MODE:-auto}"
MANUAL_SOURCE="${FOK_PI_SOURCE:-pulse}"

pkill -f fok_pi_stt.py >/dev/null 2>&1 || true

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

pick_auto_source() {
  local src=""

  if has_cmd pactl; then
    src="$(pactl list short sources 2>/dev/null | awk '/bluez_input/ {print $2; exit}')"
    if [ -n "$src" ]; then
      echo "$src"
      return 0
    fi

    src="$(pactl list short sources 2>/dev/null | awk '/analog-stereo/ && $2 !~ /\.monitor$/ {print $2; exit}')"
    if [ -n "$src" ]; then
      echo "$src"
      return 0
    fi

    src="$(pactl get-default-source 2>/dev/null || true)"
    if [ -n "$src" ]; then
      echo "$src"
      return 0
    fi
  fi

  if arecord -l 2>/dev/null | grep -qi "device"; then
    echo "default"
    return 0
  fi

  echo "pulse"
}

stream_once() {
  local src="$1"
  local rc=0

  echo "[MIC] source=$src"

  case "$src" in
    pulse|default|hw:*|plughw:*|sysdefault*)
      arecord -D "$src" -f S16_LE -r 16000 -c 1 -t raw 2>/dev/null | nc "$PC_HOST" "$PC_PORT" || rc=$?
      ;;
    *)
      if has_cmd parec; then
        parec -d "$src" --rate=16000 --channels=1 --format=s16le 2>/dev/null | nc "$PC_HOST" "$PC_PORT" || rc=$?
      else
        echo "[MIC] parec yok, source acilamadi: $src"
        rc=1
      fi
      ;;
  esac

  return "$rc"
}

while true; do
  if [ "$SOURCE_MODE" = "auto" ]; then
    SRC="$(pick_auto_source)"
  else
    SRC="$MANUAL_SOURCE"
  fi

  if ! stream_once "$SRC"; then
    echo "[MIC] reconnect after source failure: $SRC"
  fi

  sleep 1
done
