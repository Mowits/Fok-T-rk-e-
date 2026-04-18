#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PIN="${MOTOR_PIN:-18}"
DUTY="${MOTOR_DUTY:-55}"
FREQ="${MOTOR_FREQ:-1000}"
DURATION="${MOTOR_DURATION:-5}"

echo "[RUN] pin=$PIN duty=$DUTY freq=$FREQ duration=$DURATION"
sudo python3 motor_straight.py --pin "$PIN" --duty "$DUTY" --freq "$FREQ" --duration "$DURATION"
