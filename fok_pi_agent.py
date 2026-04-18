#!/usr/bin/env python3
# FOK Pi Agent - Raspberry Pi tarafinda basit komut sunucusu
# Komutlari JSON line olarak alir.

import os
import socket
import subprocess
import threading
import shutil
import json

HOST = "0.0.0.0"
PORT = 8765
TTS_CMD = os.environ.get("FOK_TTS_CMD", "").strip()
PIPER_MODEL = os.environ.get("FOK_PIPER_MODEL", "").strip()
PIPER_VOICE = os.environ.get("FOK_PIPER_VOICE", "").strip()
PIPER_RATE = os.environ.get("FOK_PIPER_RATE", "").strip()
FORCE_PIPER = os.environ.get("FOK_FORCE_PIPER", "1").strip() == "1"
MAX_TTS_CHARS = int(os.environ.get("FOK_MAX_TTS_CHARS", "0"))


def speak(text):
    if not text:
        return
    if MAX_TTS_CHARS > 0 and len(text) > MAX_TTS_CHARS:
        text = text[:MAX_TTS_CHARS].rstrip() + "..."
    # 1) Ortam degiskeniyle verilen komut
    if TTS_CMD:
        try:
            subprocess.run([TTS_CMD, text], check=True)
            print("[TTS] engine=tts_cmd ok")
            return
        except Exception as e:
            print("[TTS] tts_cmd_failed:", e)
    # 2) Piper varsa kullan (internet olabilir ama offline da calisir)
    if shutil.which("piper") and PIPER_MODEL:
        try:
            print("[TTS] engine=piper")
            # Piper -> raw audio -> aplay
            proc = subprocess.Popen(
                ["piper", "--model", PIPER_MODEL, "--output-raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            assert proc.stdin is not None
            assert proc.stdout is not None
            proc.stdin.write((text + "\n").encode("utf-8"))
            proc.stdin.flush()
            proc.stdin.close()

            rate = None
            if PIPER_RATE:
                try:
                    rate = int(PIPER_RATE)
                except Exception:
                    rate = None
            if rate is None:
                # Modelin .onnx.json dosyasindan sample rate oku
                json_path = PIPER_MODEL + ".json"
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    rate = int(cfg.get("audio", {}).get("sample_rate"))
                except Exception:
                    rate = 22050

            if shutil.which("aplay"):
                subprocess.run(
                    ["aplay", "-q", "-r", str(rate), "-f", "S16_LE", "-t", "raw"],
                    stdin=proc.stdout,
                    check=False,
                )
            else:
                proc.stdout.read()
            proc.wait(timeout=10)
            return
        except Exception as e:
            print("[TTS] piper_failed:", e)
            if FORCE_PIPER:
                return
    # 3) Sistemde espeak varsa kullan
    if FORCE_PIPER:
        print("[TTS] force_piper_on, fallback_disabled")
        return
    if shutil.which("espeak"):
        print("[TTS] engine=espeak")
        subprocess.run(["espeak", text], check=False)
        return
    # 3) Fallback
    print("[SPEAK]", text)


def handle_command(cmd):
    if cmd.get("cmd") == "speak":
        text = cmd.get("text", "")
        speak(text)
        return {"ok": True}
    return {"ok": False, "error": "unknown command"}


def client_thread(conn, addr):
    try:
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            while b"\n" in data:
                line, data = data.split(b"\n", 1)
                if not line:
                    continue
                try:
                    cmd = json.loads(line.decode("utf-8"))
                    resp = handle_command(cmd)
                except Exception as e:
                    resp = {"ok": False, "error": str(e)}
                conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
    finally:
        conn.close()


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"FOK Pi Agent dinlemede: {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
            t.start()


if __name__ == "__main__":
    main()
