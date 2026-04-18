import json
import os
import urllib.request
import urllib.error


def _build_system_prompt(user: str, profile_note: str | None) -> str:
    system = (
        "Sen FOK adli empatik ve saygili bir saglik/ev asistanisin. "
        f"Kullanici adi: {user}. "
        "Her zaman Turkce yanit ver. "
        "Kisa, net ve nazik ol. "
        "Link veya URL yazma."
    )
    if profile_note:
        system += f" Kullanici notu: {profile_note}."
    return system


def _post_json(url: str, payload: dict, headers: dict, timeout: int):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def _extract_message(obj: dict) -> str | None:
    choices = obj.get("choices", [])
    if choices:
        msg = choices[0].get("message", {}).get("content")
        if msg:
            return msg.strip()
    return None


def lm_studio_response(cfg: dict, user: str, text: str, profile_note: str | None) -> str | None:
    url = cfg.get("lm_studio_url")
    model = cfg.get("lm_studio_model", "local-model")
    timeout = int(cfg.get("lm_timeout_seconds", 8))
    max_tokens = int(cfg.get("lm_max_tokens", 220))
    if not url:
        return None
    system = _build_system_prompt(user, profile_note)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    try:
        obj = _post_json(url, payload, {"Content-Type": "application/json"}, timeout)
        msg = _extract_message(obj)
        if msg:
            return msg
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print("[LLM] lm_studio_error:", repr(e))
        return None
    return None


def openai_response(cfg: dict, user: str, text: str, profile_note: str | None) -> str | None:
    if not cfg.get("openai_enabled", False):
        return None
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    url = cfg.get("openai_url", "https://api.openai.com/v1/chat/completions")
    model = cfg.get("openai_model", "gpt-5-nano")
    timeout = int(cfg.get("openai_timeout_seconds", 12))
    max_tokens = int(cfg.get("openai_max_tokens", 220))
    system = _build_system_prompt(user, profile_note)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    try:
        obj = _post_json(
            url,
            payload,
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            timeout,
        )
        msg = _extract_message(obj)
        if msg:
            return msg
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print("[LLM] openai_error:", repr(e))
        return None
    return None


def openrouter_response(cfg: dict, user: str, text: str, profile_note: str | None) -> str | None:
    if not cfg.get("openrouter_enabled", False):
        return None
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None
    url = cfg.get("openrouter_url", "https://openrouter.ai/api/v1/chat/completions")
    model = cfg.get("openrouter_model", "anthropic/claude-3.5-sonnet")
    timeout = int(cfg.get("openrouter_timeout_seconds", 20))
    max_tokens = int(cfg.get("openrouter_max_tokens", 220))
    referer = cfg.get("openrouter_referer", "")
    title = cfg.get("openrouter_title", "FOK")
    system = _build_system_prompt(user, profile_note)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Title": title,
    }
    if referer:
        headers["HTTP-Referer"] = referer
    try:
        obj = _post_json(url, payload, headers, timeout)
        msg = _extract_message(obj)
        if msg:
            return msg
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
        print("[LLM] openrouter_error:", repr(e))
        return None
    return None


def best_available_response(cfg: dict, user: str, text: str, profile_note: str | None) -> str | None:
    return (
        openrouter_response(cfg, user, text, profile_note)
        or openai_response(cfg, user, text, profile_note)
        or lm_studio_response(cfg, user, text, profile_note)
    )


def llm_decides_web(cfg: dict, user: str, text: str, profile_note: str | None) -> bool | None:
    if not cfg.get("llm_web_decision_enabled", True):
        return None
    prompt = (
        "Asagidaki kullanici sorusu icin web aramasi gerekip gerekmedigine karar ver. "
        "Guncel, zaman-duyarli, fiyat, hava durumu, haber, skor, trafik, sefer, ucus, kur, "
        "borsa, yasal durum, yeni bilgi, bugun/simdi/son durum turu sorularda WEB_REQUIRED de. "
        "Genel bilgi, sohbet, mantik, yazma, ozetleme, ceviri gibi durumlarda NO_WEB de. "
        "Sadece tek satir ve yalnizca su iki cikistan birini ver: WEB_REQUIRED veya NO_WEB.\n\n"
        f"Kullanici sorusu: {text}"
    )
    decision = best_available_response(cfg, user, prompt, profile_note)
    if not decision:
        return None
    normalized = decision.strip().upper()
    if "WEB_REQUIRED" in normalized:
        return True
    if "NO_WEB" in normalized:
        return False
    return None
