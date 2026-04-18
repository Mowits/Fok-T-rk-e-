#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 fok_text_box.py >/tmp/fok_text_box.log 2>&1 &
python3 main.py
