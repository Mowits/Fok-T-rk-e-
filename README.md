# FOK Modular (Türkçe Sürüm)

AzerillaGTAG'e destekleri için teşekkürler.

FOK Modular; uyandırma kelimesi, STT/TTS, hatırlatıcı, ilaç takibi ve isteğe bağlı Stable Diffusion görsel üretimi içeren modüler bir asistan projesidir.

Lisans: Apache License 2.0

## Hızlı Başlangıç (PC)

```bash
cd /home/mowits/Downloads/fok_modular
./install_pc.sh
./run_pc.sh
```

## Tek Komut (PC + Pi)

```bash
cd /home/mowits/Downloads/fok_modular
./run_all_pc_pi.sh start
```

Yönetim:
- `./run_all_pc_pi.sh status`
- `./run_all_pc_pi.sh logs`
- `./run_all_pc_pi.sh live`
- `./run_all_pc_pi.sh stop`
- `./run_all_pc_pi.sh restart`
- `./run_all_pc_pi.sh sd "prompt"` (yalnızca görsel üretimi)

## Sesli Komutlar

Wake:
- `fok`
- `folk`

Örnekler:
- `fok hatirlat: doktor randevusu; 2026-03-10 14:00`
- `fok ilac: aspirin; 08:30`
- `fok ilac_sil: aspirin`
- `fok yuz_kaydet: ali`
- `fok profil: seker hastasiyim`
- `fok gorsel: kirmizi spor araba`
- `fok gorsel olustur kirmizi spor araba`

## Yüz Tanıma ve Servo Takibi

`config.json` içinde:
- `"face_enabled": true`
- `"servo_tracking_enabled": true`
- `"servo_pin": 18` (SG90 sinyal pini)

Bağlantı:
- Servo sinyal -> `GPIO18`
- Servo V+ -> harici 5V
- Servo GND -> GND
- Pi GND ile servo besleme GND ortak olmalı

Busy detector:
- `busy_window_sec` ile asistanın "meşgul" kabul edildiği süre ayarlanır.
- Meşgulken proaktif "yardım ister misin?" sorusu ertelenir.

## Stable Diffusion

Kurulum:

```bash
cd /home/mowits/Downloads/fok_modular
./install_pc_sd.sh
```

Üretim:

```bash
cd /home/mowits/Downloads/fok_modular
./run_sd.sh "kirmizi spor araba, sinematik, detayli"
```

Log:
- `/tmp/fok_sd.log`

Notlar:
- SD çalışırken VRAM boşaltmak için LM Studio otomatik olarak kapatılabilir.
- Çıktı dosyaları `outputs/sd/` altına kaydedilir.

## Geliştirme

Katkı ve güvenlik:
- `CONTRIBUTING.md`
- `SECURITY.md`

## 🧠 Yerel LLM Desteği

FOK, **yerel büyük dil modelleri (LLM)** ile çalışabilir. Bu sayede asistan tamamen **çevrim dışı (internetsiz)** olarak da kullanılabilir.

Kullanıcı istediği çalışma biçimini seçebilir:

- **Çevrim dışı mod ("mağara modu")** – tüm işlemler yerel olarak çalışır, internet kullanılmaz.
- **Çevrim içi mod** – gerektiğinde internetten bilgi çekebilir.

Bu sayede kullanıcı **gizlilik** ile **güncel bilgi** arasında istediği dengeyi kurabilir.

Özellikler:

- Yerel LLM desteği
- İsteğe bağlı internet erişimi
- Gizlilik odaklı tasarım
- Tamamen offline çalışabilme
