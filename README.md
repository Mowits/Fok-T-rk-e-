# FOK Modular (Motor-Free Assistant + Optional Stable Diffusion)

FOK Modular is a Python-based, modular assistant stack focused on:
- voice wake-word interaction (`fok`/`folk`)
- reminders and medication routines
- optional web-backed answers
- optional face registration/recognition
- optional image generation (Stable Diffusion)
- Raspberry Pi microphone/speaker bridge

## Open-Source Status

This repository is now prepared for open-source use:
- English documentation
- English default prompts/messages
- Apache License 2.0
- Contribution and security guidelines

## Quick Start (PC)

```bash
cd /home/mowits/Downloads/fok_modular
./install_pc.sh
./run_pc.sh
```

## One-Command Full Stack (PC + Pi over SSH)

```bash
cd /home/mowits/Downloads/fok_modular
chmod +x run_all_pc_pi.sh
./run_all_pc_pi.sh start
```

Management commands:
- `./run_all_pc_pi.sh status`
- `./run_all_pc_pi.sh logs`
- `./run_all_pc_pi.sh live`
- `./run_all_pc_pi.sh stop`
- `./run_all_pc_pi.sh restart`
- `./run_all_pc_pi.sh sd "prompt"` (SD only)
- `./run_all_pc_pi.sh start "prompt"` (stack + SD)

Optional environment variables:
- `FOK_PI_HOST` (default: `192.168.1.111`)
- `FOK_PI_USER` (default: `mowits`)
- `FOK_PI_KEY` (default: `/home/mowits/Downloads/fok_pi_key`)
- `FOK_PC_HOST` (default: auto-detected local IP)
- `FOK_ENABLE_PHONE_BRIDGE` (default: `1`)

## Voice Commands

Wake word:
- `fok`
- `folk`

Command examples:
- `fok remind: doctor appointment; 2026-03-10 14:00`
- `fok med: aspirin; 08:30`
- `fok med_remove: aspirin`
- `fok face_add: alice`
- `fok profile: I am diabetic`
- `fok image: red sports car at sunset`
- `fok image create red sports car`

Turkish aliases are still supported for compatibility:
- `hatirlat`, `ilac`, `ilac_sil`, `yuz_kaydet`, `profil`, `gorsel/resim`

## Stable Diffusion (PC)

Install:

```bash
cd /home/mowits/Downloads/fok_modular
chmod +x install_pc_sd.sh
./install_pc_sd.sh
```

Generate:

```bash
cd /home/mowits/Downloads/fok_modular
./run_sd.sh "red sports car, cinematic, high detail"
```

By default:
- LM Studio processes are paused before SD to reduce VRAM pressure.
- Image output is saved under `outputs/sd/`.
- `latest.png` is updated each run.

Useful SD env vars:
- `FOK_SD_MODEL`
- `FOK_SD_STEPS`
- `FOK_SD_CFG`
- `FOK_SD_WIDTH`
- `FOK_SD_HEIGHT`
- `FOK_SD_OPEN_TARGET` (`pc|pi|both|none`)
- `FOK_SD_PAUSE_LMSTUDIO` (`1|0`)
- `FOK_LMSTUDIO_RESTART_CMD` (optional restart command after SD)

Log:
- `/tmp/fok_sd.log`

## Modules

- `fok/config.py` configuration loading
- `fok/db.py` SQLite schema setup
- `fok/memory.py` long-term memory operations
- `fok/reminders.py` reminders
- `fok/meds.py` medication routines
- `fok/vision.py` face recognition/registration
- `fok/llm.py` LM Studio / OpenAI calls
- `fok/web_search.py` optional web search
- `fok/stt.py` local and remote STT integration
- `fok/behavior.py` wake/session/dialog orchestration

## Notes

- Motor control is intentionally out of scope.
- Stable Diffusion is optional and PC-side.
- OpenAI support requires `OPENAI_API_KEY`.
