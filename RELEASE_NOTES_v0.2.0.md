# Surum v0.2.0

## One Cikanlar

- `Claude 3.5 Sonnet` icin OpenRouter destegi eklendi
- OpenAI ses zinciri eklendi:
  - STT: `gpt-4o-transcribe`
  - TTS: `gpt-4o-mini-tts`
- `run_pi_all.sh` ile Pi-only calisma modu eklendi
- Elle komut gondermek icin masaustu mesaj kutusu eklendi
- Web'e bakma karari daha akilli hale getirildi
- Hava durumu icin dogrudan veri cekme yolu eklendi
- Busy detector ve proaktif yardim sinirlama eklendi
- Yuz takibi ve servo destegi eklendi
- Kisi gorulunce ilac durumunu hatirlatma mantigi eklendi
- PC/Pi ses yonlendirme ve mikrofon secimi iyilestirildi
- Duz motor test araclari eklendi

## Ana Teknik Degisiklikler

- `fok/llm.py`
  - OpenRouter saglayicisi
  - saglayici fallback sirasi
  - LLM tabanli web/no-web karari
- `fok/web_search.py`
  - sorgu normalizasyonu
  - hava durumu icin ozel veri yolu
  - Open-Meteo fallback
- `fok/behavior.py`
  - web karar akisi
  - dogrudan hava durumu cevabi
  - face reminder ve busy mantigi
- `fok_pc_whisper_stt.py`
  - OpenAI transcription yolu
  - ses RMS debug loglari
  - ayarlanabilir chunk ve threshold degerleri
- `run_all_pc_pi.sh`
  - daha saglam PC/Pi orkestrasyonu
  - ayarlanabilir Pi source yonlendirmesi
- `run_pi_mic_stream.sh`
  - auto/manual source secimi
  - PipeWire/Pulse source destegi

## Notlar

- API key'ler ortam degiskenlerinden okunur; repoda tutulmaz.
- Yanlislikla olusan yerel dosyalar ve runtime artifaktlari surum kontrolune alinmamistir.
