# FOK Modular (Turkce Surum)
!AzerillaGTAG e destekleri için teşekkürler!

FOK Modular; wake-word, STT/TTS, hatirlatici, ilac takibi ve opsiyonel Stable Diffusion gorsel uretimi iceren moduler bir asistan projesidir.

Lisans: Apache License 2.0

## Hizli Baslangic (PC)

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

Yonetim:
- `./run_all_pc_pi.sh status`
- `./run_all_pc_pi.sh logs`
- `./run_all_pc_pi.sh live`
- `./run_all_pc_pi.sh stop`
- `./run_all_pc_pi.sh restart`
- `./run_all_pc_pi.sh sd "prompt"` (sadece gorsel)

## Sesli Komutlar

Wake:
- `fok`
- `folk`

Ornekler:
- `fok hatirlat: doktor randevusu; 2026-03-10 14:00`
- `fok ilac: aspirin; 08:30`
- `fok ilac_sil: aspirin`
- `fok yuz_kaydet: ali`
- `fok profil: seker hastasiyim`
- `fok gorsel: kirmizi spor araba`
- `fok gorsel olustur kirmizi spor araba`

## Stable Diffusion

Kurulum:

```bash
cd /home/mowits/Downloads/fok_modular
./install_pc_sd.sh
```

Uretim:

```bash
cd /home/mowits/Downloads/fok_modular
./run_sd.sh "kirmizi spor araba, sinematik, detayli"
```

Log:
- `/tmp/fok_sd.log`

Notlar:
- SD calisirken VRAM bosaltmak icin LM Studio otomatik kapatilabilir.
- Cikti dosyalari `outputs/sd/` altina kaydedilir.

## Gelistirme

Katki ve guvenlik:
- `CONTRIBUTING.md`
- `SECURITY.md`
