## Katkıda Bulunma (Contributing)

FOK Modular projesine katkıda bulunduğunuz için teşekkürler.

### Geliştirme Kurulumu

```
cd /home/mowits/Downloads/fok_modular
./install_pc.sh
```

### Opsiyonel Bileşenler

Whisper STT:

```
./install_pc_whisper.sh
```

Piper TTS:

```
./install_pc_piper.sh
```

Stable Diffusion:

```
./install_pc_sd.sh
```

### Kodlama Kuralları

* Modülleri küçük ve odaklı tutun.
* Sessiz hatalar yerine açık ve anlaşılır loglar tercih edin.
* Mümkün olduğunca mevcut komut takma adları (aliases) için geriye dönük uyumluluğu koruyun.
* Gizli bilgiler, API anahtarları veya özel SSH anahtarlarını commit etmeyin.

### Doğrulama

Pull Request açmadan önce:

```
python3 -m py_compile main.py fok/*.py
bash -n run_all_pc_pi.sh run_sd.sh
```

Eğer Stable Diffusion yollarını değiştirdiyseniz ayrıca şunu da doğrulayın:

```
./run_all_pc_pi.sh sd "test prompt"
tail -n 50 /tmp/fok_sd.log
```

### Pull Request

* Açık ve anlaşılır commit mesajları kullanın.
* Davranış değişikliklerini ve yapılan tercihlerin nedenlerini açıklayın.
* Test komutlarını ve elde edilen çıktıları ekleyin.
