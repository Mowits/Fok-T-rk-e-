#!/usr/bin/env python3
import io
import json
import os
import re
import socket
import subprocess
import time
import uuid
import wave
import urllib.request
import urllib.error

try:
    import numpy as np
except Exception:
    np = None

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None
try:
    from typing import Optional
except Exception:
    Optional = None  # type: ignore

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8767
TEXT_HOST = "127.0.0.1"
TEXT_PORT = 8766
SAMPLE_RATE = 16000
CHUNK_SEC = float(os.environ.get("FOK_STT_CHUNK_SEC", "2"))
BYTES_PER_CHUNK = int(SAMPLE_RATE * 2 * CHUNK_SEC)
MIN_CHARS = 2
RMS_GATE = float(os.environ.get("FOK_STT_RMS_GATE", "60"))
DEBUG_AUDIO = os.environ.get("FOK_STT_DEBUG_AUDIO", "1") == "1"
WAKE_WORDS = ["fok", "folk", "fox", "fog", "fort", "forum", "sol"]
WAKE_FOLLOWUP_SEC = 8

MODEL_NAME = os.environ.get("FOK_STT_MODEL", "large-v3")
DEVICE = os.environ.get("FOK_STT_DEVICE", "cuda")
COMPUTE_TYPE = os.environ.get("FOK_STT_COMPUTE_TYPE", "float16")
PAUSE_LMSTUDIO = os.environ.get("FOK_STT_PAUSE_LMSTUDIO", "1") == "1"
LMSTUDIO_RESTART_CMD = os.environ.get("FOK_LMSTUDIO_RESTART_CMD", "").strip()
STT_ENGINE = os.environ.get("FOK_STT_ENGINE", "openai").strip().lower()
OPENAI_STT_URL = os.environ.get("FOK_STT_OPENAI_URL", "https://api.openai.com/v1/audio/transcriptions")
OPENAI_STT_MODEL = os.environ.get("FOK_STT_OPENAI_MODEL", "gpt-4o-transcribe")
OPENAI_STT_LANG = os.environ.get("FOK_STT_LANGUAGE", "tr")
OPENAI_TIMEOUT = int(os.environ.get("FOK_STT_OPENAI_TIMEOUT", "20"))


def send_text(text: str):
    payload = (json.dumps({"text": text}, ensure_ascii=True) + "\n").encode("utf-8")
    with socket.create_connection((TEXT_HOST, TEXT_PORT), timeout=3) as s:
        s.sendall(payload)


def _pcm_to_wav_bytes(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


def _multipart_form(fields: dict, files: list[tuple[str, str, str, bytes]]):
    boundary = "----fok-" + uuid.uuid4().hex
    lines: list[bytes] = []
    for name, value in fields.items():
        lines.append(f"--{boundary}\r\n".encode())
        lines.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        lines.append(str(value).encode())
        lines.append(b"\r\n")
    for name, filename, content_type, data in files:
        lines.append(f"--{boundary}\r\n".encode())
        lines.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        lines.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        lines.append(data)
        lines.append(b"\r\n")
    lines.append(f"--{boundary}--\r\n".encode())
    body = b"".join(lines)
    return boundary, body


def _openai_transcribe(pcm: bytes) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return ""
    wav = _pcm_to_wav_bytes(pcm)
    boundary, body = _multipart_form(
        {
            "model": OPENAI_STT_MODEL,
            "language": OPENAI_STT_LANG,
            "response_format": "json",
        },
        [("file", "audio.wav", "audio/wav", wav)],
    )
    req = urllib.request.Request(
        OPENAI_STT_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=OPENAI_TIMEOUT) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    return (obj.get("text") or "").strip()


def _rms_from_pcm(pcm: bytes) -> float:
    if np is not None:
        audio_i16 = np.frombuffer(pcm, dtype=np.int16)
        if audio_i16.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(audio_i16.astype(np.float32) ** 2)) + 1e-6)
    import array, math

    arr = array.array("h")
    arr.frombytes(pcm)
    if not arr:
        return 0.0
    s = 0.0
    for v in arr:
        s += float(v) * float(v)
    return math.sqrt(s / len(arr)) + 1e-6


def transcribe_chunk(model, pcm: bytes):
    if not pcm:
        return ""
    # Hafif RMS kapisi
    rms = _rms_from_pcm(pcm)
    if DEBUG_AUDIO:
        print(f"[PC-STT] AUDIO bytes={len(pcm)} rms={rms:.1f}")
    if rms < RMS_GATE:
        return ""
    if STT_ENGINE == "openai":
        try:
            return _openai_transcribe(pcm)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
            print("[PC-STT] openai_error:", repr(e))
            return ""

    if model is None:
        return ""
    if np is None:
        return ""
    audio_i16 = np.frombuffer(pcm, dtype=np.int16)
    if audio_i16.size == 0:
        return ""
    audio = audio_i16.astype(np.float32) / 32768.0
    segments, _ = model.transcribe(audio, language="tr", vad_filter=True, beam_size=1)
    text = " ".join(s.text.strip() for s in segments if s.text).strip()
    return text


def has_wake(text: str):
    low = text.lower().replace(",", " ").replace(".", " ").replace("!", " ").replace("?", " ")
    # STT bazen "heyfok"/"heyfolk" bitisik verebiliyor
    low = low.replace("heyfok", "hey fok").replace("heyfolk", "hey folk")
    tokens = re.findall(r"[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+", low)
    token_set = set(t.lower() for t in tokens)
    return any(w in token_set for w in WAKE_WORDS)


def should_send(text: str):
    if len(text) < MIN_CHARS:
        return False
    return True


def handle_client(conn: socket.socket, model: WhisperModel):
    print("[PC-STT] Pi baglandi")
    buf = bytearray()
    conn.settimeout(10)
    wake_open_until = 0.0
    followup_available = False
    try:
        while True:
            data = conn.recv(8192)
            if not data:
                break
            buf.extend(data)
            while len(buf) >= BYTES_PER_CHUNK:
                chunk = bytes(buf[:BYTES_PER_CHUNK])
                del buf[:BYTES_PER_CHUNK]
                text = transcribe_chunk(model, chunk)
                if not text:
                    continue
                print("[PC-STT]", text)
                if not should_send(text):
                    continue

                now = time.time()
                wake_hit = has_wake(text)
                allow = False
                reason = ""
                if wake_hit:
                    allow = True
                    reason = "wake"
                    wake_open_until = now + WAKE_FOLLOWUP_SEC
                    followup_available = True
                elif followup_available and now <= wake_open_until:
                    allow = True
                    reason = "followup"
                    followup_available = False
                else:
                    print("[PC-STT] DROP (wake/followup yok)")

                if allow:
                    try:
                        send_text(text)
                        print(f"[PC-STT] SEND ok ({reason})")
                    except Exception as e:
                        print("[PC-STT] SEND fail:", e)
    except socket.timeout:
        print("[PC-STT] timeout, baglanti kapandi")
    except Exception as e:
        print("[PC-STT] hata:", e)
    finally:
        conn.close()
        print("[PC-STT] Pi ayrildi")


def main():
    if PAUSE_LMSTUDIO:
        try:
            subprocess.run(
                ["pkill", "-f", "lm-studio|LM Studio|lmstudio/.internal/utils/node"],
                check=False,
            )
            time.sleep(2)
        except Exception:
            pass

    model = None
    if STT_ENGINE != "openai":
        if WhisperModel is None:
            raise RuntimeError("faster-whisper missing; set FOK_STT_ENGINE=openai or install deps.")
        print(f"[PC-STT] model yukleniyor... ({MODEL_NAME}, {DEVICE}, {COMPUTE_TYPE})")
        model = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE_TYPE)
    else:
        print(f"[PC-STT] OpenAI STT aktif: {OPENAI_STT_MODEL}")
    print(f"[PC-STT] chunk_sec={CHUNK_SEC} bytes_per_chunk={BYTES_PER_CHUNK} rms_gate={RMS_GATE}")
    print(f"[PC-STT] dinlemede: {LISTEN_HOST}:{LISTEN_PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((LISTEN_HOST, LISTEN_PORT))
        s.listen(1)
        while True:
            conn, _ = s.accept()
            handle_client(conn, model)
            time.sleep(0.2)

    if LMSTUDIO_RESTART_CMD:
        try:
            subprocess.Popen(LMSTUDIO_RESTART_CMD, shell=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
