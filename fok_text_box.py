#!/usr/bin/env python3
import json
import os
import socket
import tkinter as tk
from tkinter import ttk


HOST = os.environ.get("FOK_TEXTBOX_HOST", "127.0.0.1")
PORT = int(os.environ.get("FOK_TEXTBOX_PORT", "8766"))
TITLE = os.environ.get("FOK_TEXTBOX_TITLE", "FOK Text Box")


def send_text(text: str, status_var: tk.StringVar) -> None:
    text = text.strip()
    if not text:
        status_var.set("Bos mesaj gonderilmedi.")
        return
    payload = (json.dumps({"text": text}, ensure_ascii=True) + "\n").encode("utf-8")
    try:
        with socket.create_connection((HOST, PORT), timeout=2) as s:
            s.sendall(payload)
        status_var.set("Gonderildi.")
    except OSError as exc:
        status_var.set(f"Gonderilemedi: {exc}")


def main() -> None:
    root = tk.Tk()
    root.title(TITLE)
    root.geometry("420x150")
    root.resizable(False, False)

    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Mesaj").pack(anchor="w")

    text_var = tk.StringVar()
    status_var = tk.StringVar(value=f"Hedef: {HOST}:{PORT}")

    entry = ttk.Entry(frame, textvariable=text_var, font=("Sans", 12))
    entry.pack(fill="x", pady=(6, 10))
    entry.focus_set()

    def on_send(*_args) -> None:
        text = text_var.get()
        send_text(text, status_var)
        if status_var.get() == "Gonderildi.":
            text_var.set("")

    btn_row = ttk.Frame(frame)
    btn_row.pack(fill="x")
    ttk.Button(btn_row, text="Gonder", command=on_send).pack(side="left")
    ttk.Button(btn_row, text="Wake Gonder", command=lambda: (text_var.set("fok"), on_send())).pack(side="left", padx=(8, 0))

    status = ttk.Label(frame, textvariable=status_var)
    status.pack(anchor="w", pady=(10, 0))

    entry.bind("<Return>", on_send)

    root.mainloop()


if __name__ == "__main__":
    main()
