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


def lm_studio_response(cfg: dict, user: str, text: str, profile_note: str | None) -> str | None:
    url = cfg.get("lm_studio_url")
    model = cfg.get("lm_studio_model", "local-model")
    timeout = int(cfg.get("lm_timeout_seconds", 8))
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
        "max_tokens": 220,
    }
    try:
        obj = _post_json(url, payload, {"Content-Type": "application/json"}, timeout)
        choices = obj.get("choices", [])
        if choices:
            msg = choices[0].get("message", {}).get("content")
            if msg:
                return msg.strip()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
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
    system = _build_system_prompt(user, profile_note)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 220,
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
        choices = obj.get("choices", [])
        if choices:
            msg = choices[0].get("message", {}).get("content")
            if msg:
                return msg.strip()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None
    return None
