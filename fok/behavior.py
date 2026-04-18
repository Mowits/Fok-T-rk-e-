import queue
import subprocess
import time
from datetime import datetime

from .empathy import empathic_response
from .llm import best_available_response, llm_decides_web
from .memory import save_memory, get_profile_note, set_profile_note
from .meds import (
    add_or_update_med,
    disable_med,
    fetch_due_meds,
    mark_med_done_today,
    fetch_user_active_meds,
)
from .pi_bridge import send_pi_command
from .reminders import add_reminder, fetch_due_reminders, mark_reminder_done
from .web_search import normalize_query_text, normalize_web_query, weather_lookup, web_search, wants_web


def parse_reminder_command(text: str):
    # Example: "remind: take medicine; 2026-02-26 19:30" (UTC)
    low = text.lower()
    if not (low.startswith("hatirlat:") or low.startswith("remind:")):
        return None
    try:
        rest = text.split(":", 1)[1].strip()
        msg, due = rest.split(";", 1)
        msg = msg.strip()
        due = due.strip()
        datetime.fromisoformat(due)
        return msg, due
    except Exception:
        return None


def parse_med_command(text: str):
    # Example: "med: aspirin; 08:30"
    low = text.lower()
    if not (low.startswith("ilac:") or low.startswith("med:")):
        return None
    try:
        rest = text.split(":", 1)[1].strip()
        name, hm = rest.split(";", 1)
        name = name.strip()
        hm = hm.strip()
        datetime.strptime(hm, "%H:%M")
        return name, hm
    except Exception:
        return None


def parse_med_disable(text: str):
    # Example: "med_remove: aspirin"
    low = text.lower()
    if not (low.startswith("ilac_sil:") or low.startswith("med_remove:")):
        return None
    name = text.split(":", 1)[1].strip()
    return name if name else None


def parse_face_add(text: str):
    # Example: "face_add: john"
    low = text.lower()
    if not (low.startswith("yuz_kaydet:") or low.startswith("face_add:")):
        return None
    name = text.split(":", 1)[1].strip()
    return name if name else None


def parse_profile_note(text: str):
    # Example: "profile: diabetic"
    low = text.lower()
    if not (low.startswith("profil:") or low.startswith("profile:")):
        return None
    note = text.split(":", 1)[1].strip()
    return note if note else None


def parse_image_command(text: str):
    t = text.strip()
    if not t:
        return None

    def norm(s: str) -> str:
        tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        return " ".join(s.translate(tr_map).lower().split())

    n = norm(t)
    default_prompt = "sinematik detayli futuristik sahne"

    # En net format
    for p in ("gorsel:", "resim:", "image:"):
        if n.startswith(p):
            prompt = t.split(":", 1)[1].strip()
            return prompt if prompt else default_prompt

    triggers = (
        "gorsel olustur",
        "resim olustur",
        "gorsel uret",
        "resim uret",
        "image create",
        "image generate",
    )
    has_visual_word = any(w in n for w in (" gorsel", " resim", " image"))
    if not any(k in n for k in triggers) and not has_visual_word:
        return None

    # "gorsel olustur: ..." veya "hey fok gorsel olustur ..."
    if ":" in t:
        prompt = t.split(":", 1)[1].strip()
        return prompt if prompt else default_prompt

    for k in triggers:
        if k in n:
            tail = n.split(k, 1)[1].strip(" .,-")
            return tail if tail else default_prompt

    # STT bozuksa da ("gorsel ostur kirmizi araba") gorsel kelimesinden sonrasini prompt al.
    if has_visual_word:
        for w in ("gorsel", "resim", "image"):
            if w in n:
                tail = n.split(w, 1)[1].strip(" .,-")
                # "olustur/ustur/uret" gibi fiilleri temizle
                for junk in ("olustur", "ustur", "olusturur", "olusturma", "uret", "uretir"):
                    if tail.startswith(junk):
                        tail = tail[len(junk):].strip(" .,-")
                return tail if tail else default_prompt

    # Sadece "hey fok gorsel" gibi komutlarda default prompt ile uret.
    return default_prompt


def is_yes(text: str) -> bool:
    t = text.lower().strip()
    return t in {"evet", "olur", "tamam", "onay", "evet lutfen", "yes", "ok", "sure", "confirm"}


def is_no(text: str) -> bool:
    t = text.lower().strip()
    return t in {"hayir", "yok", "istemiyorum", "gerek yok", "no", "nope", "not now"}


def handle_text(
    cfg: dict,
    conn,
    user: str,
    text: str,
    face_add=None,
    pending_state: dict | None = None,
):
    if pending_state is None:
        pending_state = {}

    save_memory(conn, user, text)

    # Gorsel komutu once tetiklenip prompt bekleniyorsa, bu metni dogrudan prompt kabul et.
    if pending_state.get("image_prompt_waiting"):
        pending_state["image_prompt_waiting"] = False
        image_prompt = text.strip()
        if image_prompt:
            sd_script = cfg.get("sd_run_script", "/home/mowits/Downloads/fok_modular/run_sd.sh")
            try:
                log_path = cfg.get("sd_log_path", "/tmp/fok_sd.log")
                logf = open(log_path, "ab", buffering=0)
                subprocess.Popen(
                    ["bash", sd_script, image_prompt],
                    stdout=logf,
                    stderr=logf,
                    start_new_session=True,
                )
                return f"Generating image: {image_prompt}. Log: {log_path}", pending_state
            except Exception:
                return "Failed to start image generation. Check the SD script path.", pending_state

    # Bekleyen onaylar
    if pending_state.get("med_confirm"):
        med_id = pending_state["med_confirm"]["id"]
        if is_yes(text):
            mark_med_done_today(conn, med_id, datetime.now())
            pending_state["med_confirm"] = None
            return "Got it. I logged your medication as taken.", pending_state
        if is_no(text):
            pending_state["med_confirm"] = None
            return "Okay. Do you want me to remind you again later?", pending_state

    face_add_name = parse_face_add(text)
    med_disable = parse_med_disable(text)
    rem = parse_reminder_command(text)
    med = parse_med_command(text)
    profile_note = parse_profile_note(text)
    image_prompt = parse_image_command(text)

    if face_add_name:
        if face_add:
            ok, name = face_add(face_add_name)
            if ok:
                response = f"Done, face registered: {name}."
            else:
                response = f"Face registration failed: {name}."
        else:
            response = "Face registration is not enabled."
        return response, pending_state

    if profile_note:
        set_profile_note(conn, user, profile_note)
        return f"Saved your profile note, {user}.", pending_state

    if med_disable:
        disable_med(conn, user, med_disable)
        return f"Done {user}, removed {med_disable} from your medication list.", pending_state

    if rem:
        msg, due = rem
        add_reminder(conn, user, msg, due)
        return f"Reminder scheduled for {user}: {msg} at {due} UTC.", pending_state

    if med:
        name, hm = med
        add_or_update_med(conn, user, name, hm)
        return f"Done {user}, {name} is scheduled daily at {hm}.", pending_state

    if image_prompt:
        if not cfg.get("sd_enabled", True):
            return "Image mode is currently disabled.", pending_state
        # Prompt cok genel/varsayilan ise bir sonraki cumleyi prompt olarak iste.
        if image_prompt == "sinematik detayli futuristik sahne":
            pending_state["image_prompt_waiting"] = True
            return "Okay. What should I draw? (example: red sports car)", pending_state
        sd_script = cfg.get("sd_run_script", "/home/mowits/Downloads/fok_modular/run_sd.sh")
        try:
            log_path = cfg.get("sd_log_path", "/tmp/fok_sd.log")
            logf = open(log_path, "ab", buffering=0)
            subprocess.Popen(
                ["bash", sd_script, image_prompt],
                stdout=logf,
                stderr=logf,
                start_new_session=True,
            )
            return f"Generating image: {image_prompt}. Log: {log_path}", pending_state
        except Exception:
            return "Failed to start image generation. Check the SD script path.", pending_state

    profile = get_profile_note(conn, user)

    # Online / offline cevaplama
    heuristic_web_needed = wants_web(cfg, text)
    web_needed = llm_decides_web(cfg, user, text, profile)
    if heuristic_web_needed:
        web_needed = True
    elif web_needed is None:
        web_needed = False

    if web_needed:
        query = normalize_web_query(cfg, text)
        weather_data = weather_lookup(query) if ("hava" in query or "weather" in query) else None
        if weather_data:
            return weather_data["summary"], pending_state
        results = web_search(query, max_results=int(cfg.get("web_max_results", 3)))
        if results:
            lines = []
            for i, item in enumerate(results, start=1):
                title = item.get("title", "").strip()
                snippet = item.get("snippet", "").strip()
                if snippet:
                    lines.append(f"{i}. Title: {title}\n   Summary: {snippet}")
                else:
                    lines.append(f"{i}. Title: {title}")
            web_evidence = "\n".join(lines)
            prompt = (
                "Asagida web arama bulgulari var. "
                "Yalnizca bu bulgulara dayanarak kisa ve net Turkce cevap ver. "
                "Link veya kaynak listesi yazma.\n\n"
                f"Kullanici sorusu: {query}\n\n"
                f"Web bulgulari:\n{web_evidence}"
            )
            response = best_available_response(cfg, user, prompt, profile)
            if not response:
                snippets = [item.get("snippet", "").strip() for item in results if item.get("snippet", "").strip()]
                if snippets:
                    response = "Based on web findings: " + " ".join(snippets[:2])
                else:
                    titles = [item.get("title", "").strip() for item in results if item.get("title", "").strip()]
                    response = "Based on web findings: " + "; ".join(titles[:2])
        else:
            response = "Web search failed. Please check internet connectivity."
    else:
        response = best_available_response(cfg, user, text, profile)

    if not response:
        response = empathic_response(user, text)
    return response, pending_state


def run_loop(
    cfg: dict,
    conn,
    text_queue: queue.Queue,
    stt_fn=None,
    face_fn=None,
    face_add=None,
    face_track_fn=None,
    busy_detector=None,
):
    wake_word = cfg.get("wake_word", "fok").lower()
    wake_aliases = [w.lower() for w in cfg.get("wake_aliases", [wake_word])]
    user = cfg.get("default_user", "User")
    cooldown = int(cfg.get("cooldown_seconds", 20))
    # Wake bir kez algilandiginda, sabit sure yerine "sessizlike kadar" modu.
    # Oturum, yeni metin gelmedigi durumda idle timeout ile kapanir.
    wake_session_idle_seconds = float(cfg.get("wake_session_idle_seconds", 25))
    last_talk = 0.0
    wake_session_active = False
    wake_last_activity = 0.0
    last_reminder_check = 0.0
    last_med_check = 0.0
    last_face_check = 0.0
    last_face_track = 0.0
    last_face_name = None
    last_face_greet = 0.0
    last_help_offer = 0.0
    last_face_med_reminder = 0.0
    pending_state = {"med_confirm": None, "image_prompt_waiting": False}
    tts_guard_until = 0.0
    last_spoken_text = ""

    print("FOK Modular started. Wake word:", wake_word)
    print("Commands:")
    print("- text input (when STT is disabled)")
    print("- 'remind: message; YYYY-MM-DD HH:MM' (UTC)")
    print("- 'med: name; HH:MM' (daily)")
    print("- 'med_remove: name'")
    print("- 'face_add: name'")
    print("- 'profile: short note'")
    print("- 'exit' to quit")

    def has_wake(text: str) -> bool:
        t = text.lower()
        return any(w in t for w in wake_aliases)

    def strip_wake(text: str) -> str:
        t = text
        for w in wake_aliases:
            t = t.replace(w, "")
        return t.strip()

    def is_busy_now() -> bool:
        if not busy_detector:
            return False
        try:
            if callable(busy_detector):
                return bool(busy_detector())
            if hasattr(busy_detector, "is_busy"):
                return bool(busy_detector.is_busy())
        except Exception:
            return False
        return False

    def say(text: str):
        nonlocal tts_guard_until, last_spoken_text
        print("FOK:", text)
        last_spoken_text = (text or "").lower()
        # Hoparlorden cikan TTS'nin tekrar mikrofondan STT'ye dusmesini azalt.
        guard_sec = min(60.0, max(6.0, len(last_spoken_text) / 10.0))
        tts_guard_until = time.time() + guard_sec
        if busy_detector and hasattr(busy_detector, "mark_busy_for"):
            try:
                busy_detector.mark_busy_for(guard_sec)
            except Exception:
                pass
        try:
            send_pi_command(cfg["pi_host"], cfg["pi_port"], {"cmd": "speak", "text": text})
        except Exception as e:
            print("Pi command error:", e)

    try:
        while True:
            now = time.time()

            # Hatirlatmalar
            if cfg.get("reminders_enabled", False) and now - last_reminder_check >= cfg.get("reminder_check_seconds", 15):
                last_reminder_check = now
                for rid, r_user, r_text, due_at in fetch_due_reminders(conn):
                    msg = f"{r_user}, {r_text} hatirlatmasi geldi."
                    print(f"[REMINDER] {r_user}: {r_text} (due: {due_at} UTC)")
                    say(msg)
                    mark_reminder_done(conn, rid)

            # Gunluk ilac rutinleri
            if cfg.get("meds_enabled", False) and now - last_med_check >= 20:
                last_med_check = now
                now_local = datetime.now()
                for mid, m_user, m_name in fetch_due_meds(conn, now_local):
                    msg = f"{m_user}, this is your medication reminder for {m_name}."
                    print(f"[MED] {m_user}: {m_name}")
                    say(msg)
                    if cfg.get("med_confirm_required", True):
                        pending_state["med_confirm"] = {"id": mid, "user": m_user, "name": m_name}
                    else:
                        mark_med_done_today(conn, mid, now_local)

            # Kisi tanima
            if face_track_fn and (now - last_face_track >= cfg.get("face_track_interval", 0.25)):
                last_face_track = now
                try:
                    face_track_fn()
                except Exception:
                    pass

            if face_fn and (now - last_face_check >= cfg.get("face_check_seconds", 5)):
                last_face_check = now
                name = face_fn()
                if name and name != last_face_name and (now - last_face_greet >= cfg.get("face_greet_cooldown", 30)):
                    last_face_name = name
                    user = name
                    last_face_greet = now
                    greet = f"Hello {name}, welcome back."
                    print("[FACE] Detected:", name)
                    say(greet)

                # Yuz goruldugunde kisiye ilac listesini hatirlat (opsiyonel)
                if (
                    name
                    and cfg.get("face_med_reminder_on_recognition", True)
                    and (now - last_face_med_reminder >= cfg.get("face_med_reminder_cooldown", 120))
                ):
                    meds = fetch_user_active_meds(conn, name)
                    if meds:
                        today = datetime.now().strftime("%Y-%m-%d")
                        pending = []
                        for med_name, hm, last_date in meds:
                            status = "alinmadi" if last_date != today else "alindi"
                            pending.append(f"{med_name} ({hm}, {status})")
                        med_text = ", ".join(pending[:3])
                        if len(pending) > 3:
                            med_text += ", ve digerleri"
                        say(f"{name}, ilac durumun: {med_text}.")
                        last_face_med_reminder = now

                # Yardim teklif etme (busy degilse ve bir sure etkinlik yoksa)
                if name and (now - last_help_offer >= 120):
                    if not is_busy_now():
                        say("Do you want any help?")
                        last_help_offer = now

            # Metin alma
            text = ""
            if stt_fn:
                text = stt_fn()
            elif text_queue is not None:
                try:
                    text = text_queue.get(timeout=0.2)
                except queue.Empty:
                    text = ""
            else:
                text = input("> ").strip()

            if not text:
                continue
            if busy_detector and hasattr(busy_detector, "mark_activity"):
                try:
                    busy_detector.mark_activity()
                except Exception:
                    pass
            if text.lower() in {"cikis", "exit", "quit"}:
                break

            print("> ", text)

            now_talk = time.time()
            if now_talk < tts_guard_until and not pending_state.get("image_prompt_waiting"):
                print("[STT] TTS feedback filter: text skipped.")
                continue
            if wake_session_active and (now_talk - wake_last_activity > wake_session_idle_seconds):
                wake_session_active = False
                print("[Wake] Session closed due to inactivity.")
            wake_detected = has_wake(text)

            # Wake algilanirsa asistani belirli bir sure uyanik tut.
            if wake_detected:
                wake_session_active = True
                wake_last_activity = now_talk
                cleaned = normalize_query_text(strip_wake(text.lower()))
                if not cleaned:
                    # Sadece wake denildiyse komut bekleme moduna gir.
                    print("[Wake] Voice session opened.")
                    continue
            elif wake_session_active:
                cleaned = normalize_query_text(text.lower().strip())
                wake_last_activity = now_talk
            else:
                print("[Sleep] Wake word not detected.")
                continue

            # STT cop/yarim kelime spamini azalt
            if len(cleaned.strip()) < 4 or cleaned.strip().endswith("-"):
                print("[STT] Short/noisy text skipped.")
                continue
            # Modelin kendi cevabini tekrar algilama durumunu ele.
            if last_spoken_text and len(cleaned) > 8 and cleaned in last_spoken_text:
                print("[STT] Echo text skipped.")
                continue

            # Wake oturumu disinda cooldown uygula.
            if (not wake_session_active) and (now_talk - last_talk < cooldown):
                print("[Cooldown] Waiting before next command.")
                continue

            last_talk = now_talk

            response, pending_state = handle_text(
                cfg,
                conn,
                user,
                cleaned,
                face_add=face_add,
                pending_state=pending_state,
            )
            say(response)

    except KeyboardInterrupt:
        print("\n[EXIT] Stopped.")
