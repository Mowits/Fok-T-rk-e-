import html
import re
import urllib.parse
import urllib.request
import json


def normalize_query_text(text: str) -> str:
    t = " ".join((text or "").strip().split())
    t = re.sub(r"^[,.;:!?-]+\s*", "", t)
    fixes = {
        " ran fiyat": " ram fiyat",
        " ran ": " ram ",
        " ramlari": " ram'leri",
        " istanblun ": " istanbul ",
        " istanbln ": " istanbul ",
        " istanbulun ": " istanbul ",
        " ankaranin ": " ankara ",
        " izmirin ": " izmir ",
        " ekran karti ": " ekran karti ",
        " islemci ": " islemci ",
        " ssd ": " ssd ",
    }
    padded = f" {t.lower()} "
    for wrong, correct in fixes.items():
        padded = padded.replace(wrong, correct)
    return " ".join(padded.split())


def web_search(query: str, max_results: int = 3, timeout: int = 6):
    url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(url, headers={"User-Agent": "FOK/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html_text = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return []
    title_matches = list(re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text))
    snippet_matches = list(re.finditer(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html_text))
    results = []
    for i, m in enumerate(title_matches):
        link = html.unescape(m.group(1))
        title = re.sub(r"<.*?>", "", m.group(2))
        title = html.unescape(title).strip()
        snippet = ""
        if i < len(snippet_matches):
            snippet = re.sub(r"<.*?>", "", snippet_matches[i].group(1))
            snippet = html.unescape(snippet).strip()
        results.append({"title": title, "snippet": snippet, "url": link})
        if len(results) >= max_results:
            break
    return results


def extract_weather_location(text: str) -> str | None:
    t = normalize_query_text(text)
    t = re.sub(r"\b(hey|fok|folk|fox|fog|fort|forum|sol)\b", " ", t)
    t = re.sub(r"\b(hava|weather|durumu|bugun|simdi|nasil|kac|derece|olarak|suan|şuan|anlik)\b", " ", t)
    t = t.replace("'un", " ").replace("'in", " ").replace("'da", " ").replace("'de", " ")
    t = re.sub(r"\b(istanbulda)\b", "istanbul", t)
    t = re.sub(r"\b(ankarada)\b", "ankara", t)
    t = re.sub(r"\b(izmirde)\b", "izmir", t)
    t = " ".join(t.split())
    if not t:
        return None
    return t


def _weather_code_desc(code: int) -> str:
    mapping = {
        0: "Acik",
        1: "Cogunlukla acik",
        2: "Parcali bulutlu",
        3: "Bulutlu",
        45: "Sisli",
        48: "Kirağıli sis",
        51: "Hafif cise",
        53: "Cise",
        55: "Yogun cise",
        61: "Hafif yagmur",
        63: "Yagmur",
        65: "Yogun yagmur",
        71: "Hafif kar",
        73: "Kar",
        75: "Yogun kar",
        80: "Sağanak",
        81: "Kuvvetli sağanak",
        82: "Cok kuvvetli sağanak",
        95: "Gok gurultulu firtina",
    }
    return mapping.get(code, f"Hava kodu {code}")


def _open_meteo_weather(location: str, timeout: int = 8) -> dict | None:
    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urllib.parse.urlencode({"name": location, "count": 1, "language": "tr", "format": "json"})
    )
    req = urllib.request.Request(geo_url, headers={"User-Agent": "FOK/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        geo = json.loads(resp.read().decode("utf-8", errors="ignore"))
    results = geo.get("results") or []
    if not results:
        return None
    item = results[0]
    lat = item.get("latitude")
    lon = item.get("longitude")
    if lat is None or lon is None:
        return None
    weather_url = (
        "https://api.open-meteo.com/v1/forecast?"
        + urllib.parse.urlencode(
            {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "timezone": "auto",
            }
        )
    )
    req = urllib.request.Request(weather_url, headers={"User-Agent": "FOK/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        obj = json.loads(resp.read().decode("utf-8", errors="ignore"))
    current = obj.get("current") or {}
    area_name = (item.get("name") or location).strip()
    region_name = (item.get("admin1") or "").strip()
    lines = [f"Konum: {area_name}" + (f", {region_name}" if region_name else "")]
    if "temperature_2m" in current:
        lines.append(f"Sicaklik: {current['temperature_2m']}C")
    if "apparent_temperature" in current:
        lines.append(f"Hissedilen: {current['apparent_temperature']}C")
    if "weather_code" in current:
        lines.append(f"Durum: {_weather_code_desc(int(current['weather_code']))}")
    if "relative_humidity_2m" in current:
        lines.append(f"Nem: %{current['relative_humidity_2m']}")
    if "wind_speed_10m" in current:
        lines.append(f"Ruzgar: {current['wind_speed_10m']} km/sa")
    return {"location": area_name, "summary": "\n".join(lines)}


def weather_lookup(text: str, timeout: int = 8) -> dict | None:
    location = extract_weather_location(text) or "Istanbul"
    url = "https://wttr.in/" + urllib.parse.quote(location) + "?format=j1"
    req = urllib.request.Request(url, headers={"User-Agent": "FOK/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            obj = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception as e:
        print("[WEB] wttr_error:", repr(e))
        try:
            return _open_meteo_weather(location, timeout=timeout)
        except Exception as e2:
            print("[WEB] open_meteo_error:", repr(e2))
            return None

    current = (obj.get("current_condition") or [{}])[0]
    nearest = (obj.get("nearest_area") or [{}])[0]
    area_name = (((nearest.get("areaName") or [{}])[0]).get("value") or location).strip()
    region_name = (((nearest.get("region") or [{}])[0]).get("value") or "").strip()
    desc = (((current.get("weatherDesc") or [{}])[0]).get("value") or "").strip()
    feels = current.get("FeelsLikeC", "")
    temp = current.get("temp_C", "")
    humidity = current.get("humidity", "")
    wind = current.get("windspeedKmph", "")

    lines = [f"Konum: {area_name}" + (f", {region_name}" if region_name else "")]
    if temp:
        lines.append(f"Sicaklik: {temp}C")
    if feels:
        lines.append(f"Hissedilen: {feels}C")
    if desc:
        lines.append(f"Durum: {desc}")
    if humidity:
        lines.append(f"Nem: %{humidity}")
    if wind:
        lines.append(f"Ruzgar: {wind} km/sa")

    summary = "\n".join(lines)
    if summary.strip() == f"Konum: {area_name}" + (f", {region_name}" if region_name else ""):
        try:
            return _open_meteo_weather(location, timeout=timeout)
        except Exception as e:
            print("[WEB] open_meteo_error:", repr(e))
    return {"location": area_name, "summary": summary}


def wants_web(cfg: dict, text: str) -> bool:
    if not cfg.get("web_enabled", True):
        return False
    t = normalize_query_text(text)
    words = cfg.get("web_trigger_words", ["web:", "search:", "google", "lookup:", "internetten", "ara:"])
    if any(k in t for k in words):
        return True

    # Otomatik karar: zaman-hassas ve guncel bilgi gerektiren niyetler.
    web_signals = cfg.get("web_auto_keywords") or [
        "bugun", "today", "guncel", "latest", "son durum", "simdi",
        "hava durumu", "weather", "kur", "dolar", "euro", "btc", "bitcoin",
        "borsa", "hisse", "fiyat", "price", "haber", "news", "skor", "score",
        "mac", "match", "trafik", "yol durumu", "ucus", "flight",
        "sefer", "otobus", "tren", "faiz", "enflasyon",
    ]
    if any(s in t for s in web_signals):
        return True
    if "hava durum" in t:
        return True
    if "fiyatlar" in t or "fiyati" in t or "kac para" in t:
        return True

    # Hava durumu ifadeleri: "istanbul hava", "ankara'da hava"
    if re.search(r"\b([a-zA-ZçğıöşüÇĞİÖŞÜ]{3,})\s+(hava|weather)\b", t):
        return True
    if re.search(r"\b(hava|weather)\s+durumu\b", t):
        return True

    return False


def normalize_web_query(cfg: dict, text: str) -> str:
    t = normalize_query_text(text)
    for w in cfg.get("web_trigger_words", ["web:", "search:", "google", "lookup:", "internetten", "ara:"]):
        t = t.replace(w, " ")
    return " ".join(t.split())
