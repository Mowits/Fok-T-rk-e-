#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export FOK_STT_MODEL="${FOK_STT_MODEL:-large-v3}"
export FOK_STT_DEVICE="${FOK_STT_DEVICE:-cuda}"
export FOK_STT_COMPUTE_TYPE="${FOK_STT_COMPUTE_TYPE:-float16}"
export FOK_STT_PAUSE_LMSTUDIO="${FOK_STT_PAUSE_LMSTUDIO:-1}"
export FOK_STT_ENGINE="${FOK_STT_ENGINE:-openai}"
export FOK_STT_OPENAI_MODEL="${FOK_STT_OPENAI_MODEL:-gpt-4o-transcribe}"
export FOK_STT_LANGUAGE="${FOK_STT_LANGUAGE:-tr}"
export FOK_STT_CHUNK_SEC="${FOK_STT_CHUNK_SEC:-2}"
export FOK_STT_RMS_GATE="${FOK_STT_RMS_GATE:-60}"
export FOK_STT_DEBUG_AUDIO="${FOK_STT_DEBUG_AUDIO:-1}"
python3 fok_pc_whisper_stt.py
