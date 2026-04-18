#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

ACTION="${1:-start}"
SD_PROMPT="${2:-}"

FOK_PI_HOST="${FOK_PI_HOST:-192.168.1.111}"
FOK_PI_USER="${FOK_PI_USER:-mowits}"
FOK_PI_KEY="${FOK_PI_KEY:-/home/mowits/fok_pi_key}"
FOK_PI_SOURCE_MODE="${FOK_PI_SOURCE_MODE:-manual}"
FOK_PI_SOURCE="${FOK_PI_SOURCE:-alsa_input.usb-Sonix_Technology_Co.__Ltd._USB_2.0_Camera_SN0001-02.analog-stereo}"

detect_pc_ip() {
  ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}'
}

PC_IP_DEFAULT="$(detect_pc_ip || true)"
FOK_PC_HOST="${FOK_PC_HOST:-${PC_IP_DEFAULT:-192.168.1.101}}"

PC_STACK_LOG="${FOK_PC_STACK_LOG:-/tmp/fok_pc_stack.log}"
PC_WHISPER_LOG="${FOK_PC_WHISPER_LOG:-/tmp/fok_pc_whisper.log}"
PC_PHONE_LOG="${FOK_PC_PHONE_LOG:-/tmp/fok_phone_bridge.log}"
PC_HTTP_LOG="${FOK_PC_HTTP_LOG:-/tmp/fok_http_gateway.log}"
PI_LOG="${FOK_PI_LOG:-/tmp/fok_pi_mic_stream.log}"
FOK_ENABLE_PHONE_BRIDGE="${FOK_ENABLE_PHONE_BRIDGE:-1}"
FOK_PUBLIC_TCP="${FOK_PUBLIC_TCP:-1}"
FOK_PUBLIC_TCP_PORT="${FOK_PUBLIC_TCP_PORT:-8766}"
FOK_HTTP_GATEWAY="${FOK_HTTP_GATEWAY:-1}"
FOK_HTTP_PORT="${FOK_HTTP_PORT:-8877}"

SSH_BASE=(ssh -i "$FOK_PI_KEY" -o StrictHostKeyChecking=no "${FOK_PI_USER}@${FOK_PI_HOST}")

ssh_try() {
  local remote_cmd="$1"
  "${SSH_BASE[@]}" "$remote_cmd"
}

start_pi_remote() {
  "${SSH_BASE[@]}" bash -s -- "$FOK_PC_HOST" "$PI_LOG" "$FOK_PI_SOURCE_MODE" "$FOK_PI_SOURCE" <<'EOS'
set -e
PC_HOST="$1"
PI_LOG="$2"
PI_SOURCE_MODE="$3"
PI_SOURCE="$4"
chmod +x /home/mowits/Downloads/fok_modular/run_pi_mic_stream.sh >/dev/null 2>&1 || true
pkill -f 'run_pi_mic_stream.sh|arecord -D' >/dev/null 2>&1 || true
nohup env FOK_PC_HOST="$PC_HOST" FOK_PI_SOURCE_MODE="$PI_SOURCE_MODE" FOK_PI_SOURCE="$PI_SOURCE" /home/mowits/Downloads/fok_modular/run_pi_mic_stream.sh >"$PI_LOG" 2>&1 </dev/null &
sleep 1
ps -ef | grep -E 'run_pi_mic_stream.sh|arecord -D|parec ' | grep -v grep || true
EOS
}

start_all() {
  echo "[START] PC stack basliyor..."
  pkill -f 'run_pc_stack_pc_piper.sh|main.py|fok_pc_whisper_stt.py|fok_pi_agent.py|phone_bridge_server.py|fok_text_box.py' >/dev/null 2>&1 || true

  nohup bash -lc "cd '$BASE_DIR' && PYTHONUNBUFFERED=1 ./run_pc_stack_pc_piper.sh" >"$PC_STACK_LOG" 2>&1 &
  nohup bash -lc "cd '$BASE_DIR' && source .venv_whisper/bin/activate && PYTHONUNBUFFERED=1 ./run_pc_whisper_stt.sh" >"$PC_WHISPER_LOG" 2>&1 &
  if [[ "$FOK_ENABLE_PHONE_BRIDGE" == "1" ]]; then
    nohup bash -lc "cd '$BASE_DIR' && PYTHONUNBUFFERED=1 python3 phone_bridge_server.py" >"$PC_PHONE_LOG" 2>&1 &
    echo "[START] Phone bridge: http://${FOK_PC_HOST}:8770"
  fi
  if [[ "$FOK_HTTP_GATEWAY" == "1" ]]; then
    nohup bash -lc "cd '$BASE_DIR' && PYTHONUNBUFFERED=1 python3 fok_http_gateway.py" >"$PC_HTTP_LOG" 2>&1 &
    echo "[START] HTTP gateway: http://${FOK_PC_HOST}:${FOK_HTTP_PORT}/text"
  fi
  if [[ "$FOK_PUBLIC_TCP" == "1" ]]; then
    echo "[START] Public TCP (remote STT ingest): 0.0.0.0:${FOK_PUBLIC_TCP_PORT}"
  fi

  sleep 2
  echo "[START] Pi mic stream ssh ile baslatiliyor... (PC_HOST=$FOK_PC_HOST)"
  if ! ssh_try "echo PI_SSH_OK" >/dev/null 2>&1; then
    echo "[WARN] Pi SSH ulasilamiyor: ${FOK_PI_USER}@${FOK_PI_HOST}"
  elif ! start_pi_remote; then
    echo "[WARN] Pi baslatma adimi basarisiz. SSH/Network kontrol et: ${FOK_PI_USER}@${FOK_PI_HOST}"
  fi

  echo "[OK] Tum servisler baslatildi."
  status_all
}

stop_all() {
  echo "[STOP] PC prosesleri durduruluyor..."
  pkill -f 'run_pc_stack_pc_piper.sh|main.py|fok_pc_whisper_stt.py|fok_pi_agent.py|phone_bridge_server.py|fok_text_box.py' >/dev/null 2>&1 || true

  echo "[STOP] Pi prosesleri durduruluyor..."
  if ! ssh_try "pkill -f 'run_pi_mic_stream.sh|arecord -D' >/dev/null 2>&1 || true"; then
    echo "[WARN] Pi'ye baglanilamadi, uzak stop atlandi."
  fi

  echo "[OK] Durduruldu."
}

status_all() {
  echo "=== PC ==="
  pgrep -af 'run_pc_stack_pc_piper.sh|main.py|fok_pc_whisper_stt.py|fok_pi_agent.py|phone_bridge_server.py|fok_text_box.py' || echo "PC: calisan proses yok"

  echo "=== PI (${FOK_PI_HOST}) ==="
  if ! ssh_try "ps -ef | grep -E 'run_pi_mic_stream.sh|arecord -D' | grep -v grep || echo 'PI: calisan proses yok'"; then
    echo "PI: SSH baglantisi yok (${FOK_PI_USER}@${FOK_PI_HOST})"
  fi
}

logs_all() {
  echo "=== PC stack log ($PC_STACK_LOG) ==="
  tail -n 40 "$PC_STACK_LOG" || true
  echo
  echo "=== PC whisper log ($PC_WHISPER_LOG) ==="
  tail -n 40 "$PC_WHISPER_LOG" || true
  echo
  echo "=== PC phone log ($PC_PHONE_LOG) ==="
  tail -n 40 "$PC_PHONE_LOG" || true
  echo
  echo "=== PC http log ($PC_HTTP_LOG) ==="
  tail -n 40 "$PC_HTTP_LOG" || true
  echo
  echo "=== PI log ($PI_LOG) ==="
  if ! ssh_try "tail -n 40 '$PI_LOG' || true"; then
    echo "PI: log alinamadi (SSH baglantisi yok)."
  fi
}

live_logs() {
  echo "[LIVE] Ctrl+C ile cikis"
  touch "$PC_STACK_LOG" "$PC_WHISPER_LOG" "$PC_PHONE_LOG" || true

  (tail -n 20 -F "$PC_STACK_LOG"   | sed -u 's/^/[PC-STACK] /') &
  P1=$!
  (tail -n 20 -F "$PC_WHISPER_LOG" | sed -u 's/^/[PC-STT] /') &
  P2=$!
  (tail -n 20 -F "$PC_PHONE_LOG"   | sed -u 's/^/[PHONE] /') &
  P3=$!

  P4=""
  if ssh_try "echo PI_SSH_OK" >/dev/null 2>&1; then
    (ssh_try "tail -n 20 -F '$PI_LOG' 2>/dev/null || true" | sed -u 's/^/[PI-MIC] /') &
    P4=$!
  else
    echo "[LIVE] PI baglantisi yok: ${FOK_PI_USER}@${FOK_PI_HOST}"
  fi

  cleanup_live() {
    kill "$P1" "$P2" "$P3" >/dev/null 2>&1 || true
    if [[ -n "$P4" ]]; then kill "$P4" >/dev/null 2>&1 || true; fi
  }
  trap cleanup_live EXIT INT TERM
  wait
}

run_sd_once() {
  local prompt="$1"
  if [[ -z "$prompt" ]]; then
    return 0
  fi
  echo "[SD] Uretim basliyor..."
  nohup bash -lc "cd '$BASE_DIR' && ./run_sd.sh \"$prompt\"" >/tmp/fok_sd.log 2>&1 &
  echo "[SD] Baslatildi. Log: /tmp/fok_sd.log"
}

case "$ACTION" in
  start) start_all; run_sd_once "$SD_PROMPT" ;;
  stop) stop_all ;;
  restart) stop_all; start_all; run_sd_once "$SD_PROMPT" ;;
  status) status_all ;;
  logs) logs_all ;;
  live) live_logs ;;
  sd) run_sd_once "$SD_PROMPT" ;;
  *)
    echo "Kullanim: $0 {start|stop|restart|status|logs|live|sd} [sd_prompt]"
    exit 1
    ;;
esac
