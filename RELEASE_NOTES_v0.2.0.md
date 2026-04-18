# Sürüm v0.2.0

## Öne Çıkanlar

- `Claude 3.5 Sonnet` için OpenRouter desteği eklendi
- OpenAI ses zinciri eklendi:
  - STT: `gpt-4o-transcribe`
  - TTS: `gpt-4o-mini-tts`
- `run_pi_all.sh` ile yalnızca Pi üzerinde çalışma modu eklendi
- Elle komut göndermek için masaüstü mesaj kutusu eklendi
- Web'e bakma kararı daha akıllı hâle getirildi
- Hava durumu için doğrudan veri çekme yolu eklendi
- Meşguliyet algılama ve proaktif yardım sınırlaması eklendi
- Yüz takibi ve servo desteği eklendi
- Kişi görülünce ilaç durumunu hatırlatma mantığı eklendi
- PC/Pi ses yönlendirme ve mikrofon seçimi iyileştirildi
- Düz motor test araçları eklendi

## Ana Teknik Değişiklikler

- `fok/llm.py`
  - OpenRouter sağlayıcısı
  - sağlayıcı fallback sırası
  - LLM tabanlı web/no-web kararı
- `fok/web_search.py`
  - sorgu normalizasyonu
  - hava durumu için özel veri yolu
  - Open-Meteo fallback
- `fok/behavior.py`
  - web karar akışı
  - doğrudan hava durumu cevabı
  - yüz hatırlatma ve meşguliyet mantığı
- `fok_pc_whisper_stt.py`
  - OpenAI transcription yolu
  - ses RMS hata ayıklama logları
  - ayarlanabilir chunk ve eşik değerleri
- `run_all_pc_pi.sh`
  - daha sağlam PC/Pi orkestrasyonu
  - ayarlanabilir Pi source yönlendirmesi
- `run_pi_mic_stream.sh`
  - otomatik / manuel source seçimi
  - PipeWire/Pulse source desteği

## Notlar

- API anahtarları ortam değişkenlerinden okunur; repoda tutulmaz.
- Yanlışlıkla oluşan yerel dosyalar ve çalışma zamanı artifaktları sürüm kontrolüne alınmamıştır.
