#!/usr/bin/env python3
import os
import queue

from fok.behavior import run_loop
from fok.busy import BusyDetector
from fok.config import load_config, resolve_db_path
from fok.db import init_db
from fok.stt import start_remote_stt_server, try_init_whisper
from fok.vision import try_init_face, try_init_emotion


def main():
    base = os.path.dirname(__file__)
    cfg_path = os.environ.get("FOK_CONFIG", os.path.join(base, "config.json"))
    cfg = load_config(cfg_path)
    db_path = resolve_db_path(cfg_path, cfg)
    conn = init_db(db_path)

    text_queue = queue.Queue()
    stt_fn = try_init_whisper(cfg)
    if cfg.get("stt_enabled", False) and not stt_fn:
        print("[STT] Whisper baslatilamadi. Gerekli kutuphaneleri kur.")

    if cfg.get("remote_stt_enabled", False):
        start_remote_stt_server(cfg, text_queue)

    face_ctx = try_init_face(cfg)
    face_fn = face_ctx["identify"] if face_ctx else None
    face_add = face_ctx["add"] if face_ctx else None
    face_track = face_ctx.get("track") if face_ctx else None
    if cfg.get("face_enabled", False) and not face_fn:
        print("[FACE] Yuz algilama baslatilamadi. OpenCV/face_recognition ve faces_dir gerekli.")

    emotion_fn = try_init_emotion(cfg)
    if cfg.get("emotion_enabled", False) and not emotion_fn:
        print("[EMOTION] Duygu analizi modeli bagli degil.")

    run_loop(
        cfg,
        conn,
        text_queue if cfg.get("remote_stt_enabled", False) else None,
        stt_fn=stt_fn,
        face_fn=face_fn,
        face_add=face_add,
        face_track_fn=face_track,
        busy_detector=BusyDetector(float(cfg.get("busy_window_sec", 45))),
    )


if __name__ == "__main__":
    main()
