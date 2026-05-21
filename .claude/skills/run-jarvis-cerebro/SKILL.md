---
name: run-jarvis-cerebro
description: Run, start, launch, test, or smoke-test the Jarvis multi-agent AI system. Covers the FastAPI server (jarvis_api.py), interactive harness CLI (harness.py), and smoke testing live endpoints with curl.
---

Jarvis Cerebro is a local multi-agent AI system on Apple Silicon (MLX). It exposes a **FastAPI server** on port 5555, an **interactive CLI harness**, and several utility scripts. The agent path is curl-based smoke testing against the live API. Paths below are relative to the repo root.

## Prerequisites

- Docker Desktop must be running before any `harness.py` or `jarvis_api.py` invocation that hits the CODIGO flow (spawns `DockerSandbox`).
- Python venv at `.venv/` — always activate first.
- Models are cached in `~/.cache/huggingface/` after first download; first startup fetches ~4 GB.

```bash
source .venv/bin/activate
```

## Run (agent path) — API server + curl smoke test

**Start the server** (models load in ~3–5 s once cached; ~60 s on first run while downloading):

```bash
source .venv/bin/activate
python -m uvicorn jarvis_api:app --host 0.0.0.0 --port 5555 &
```

**Wait until ready:**

```bash
until curl -sf http://localhost:5555/ > /dev/null 2>&1; do sleep 2; done
echo "ready"
```

**Run the smoke test** (all three endpoints):

```bash
bash .claude/skills/run-jarvis-cerebro/smoke.sh
```

The smoke script (`smoke.sh`) tests:
1. `GET /` — health check, asserts `"status":"online"`
2. `POST /chat {"tarea":"hola"}` — RAG chat, asserts non-empty `respuesta`
3. `POST /siri {"tarea":"hola"}` — TTS-optimized endpoint, asserts non-empty plain-text response

**Ad-hoc curl calls:**

```bash
# Chat (RAG only, no web search or code exec)
curl -s -X POST http://localhost:5555/chat \
  -H "Content-Type: application/json" \
  -d '{"tarea":"explica qué es chromadb"}'

# Full planning + multi-agent pipeline
curl -s -X POST http://localhost:5555/pensar \
  -H "Content-Type: application/json" \
  -d '{"tarea":"investiga qué es MLX de Apple"}'

# Deep iterative research
curl -s -X POST http://localhost:5555/investigar \
  -H "Content-Type: application/json" \
  -d '{"tarea":"ventajas del hardware Apple Silicon para ML"}'

# Siri-optimized (returns plain text, not JSON)
curl -s -X POST http://localhost:5555/siri \
  -H "Content-Type: application/json" \
  -d '{"tarea":"qué temperatura hace hoy"}'
```

**Stop the server:**

```bash
kill %1   # or kill <PID>
```

## Run (human path) — interactive CLI

```bash
source .venv/bin/activate
python harness.py --interactivo   # loop: type task, press Enter, type "salir" to quit
python harness.py "investiga X"   # one-shot task
```

## Utility scripts

```bash
# Ingest all PDFs from Biblioteca/ into ChromaDB
python asimilador_libros.py

# Ingest a URL into ChromaDB
python asimilador_web.py

# Inspect / delete ChromaDB entries
python gestor_memoria.py

# Voice interface (requires microphone; needs API server running on :5555)
python jarvis_voz.py
```

## Direct invocation (no model load)

Test memory and chip loading without loading any LLM:

```bash
source .venv/bin/activate
python -c "
from herramientas import buscar_memoria, guardar_en_memoria, listar_workspace, cargar_chip
guardar_en_memoria('test', {'autor': 'dev'}, doc_id='dev_test_001')
print(buscar_memoria('test', n=1)[:80])
print('workspace:', listar_workspace())
print('chip bytes:', len(cargar_chip('chip_coder')))
"
```

## Gotchas

- **`OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES`** — already set in `harness.py` before any MLX import. If you import `harness` or `neuronas` in a subprocess without this, you get a macOS segfault.
- **`mp.set_start_method("spawn", force=True)`** — required at the `__main__` guard. Omitting it causes MLX + multiprocessing to deadlock on macOS.
- **`/siri` returns plain text, not JSON** — `response.text`, not `response.json()`. The `puente_siri.py` client does `.strip().strip('"')` on the raw body.
- **`/pensar` and `/investigar` spawn `DockerSandbox`** for CODIGO steps — Docker Desktop must be running or those endpoints time out silently.
- **First startup downloads ~4 GB** — `Qwen2.5-7B-Instruct-4bit` + `Llama-3.2-3B-Instruct-4bit` via HuggingFace Hub. Subsequent starts use the local cache and finish in 3–5 s.
- **`tester` evaluates with `EXITO_TOTAL` but harness checks for substring `EXITO`** — if you change the tester prompt, keep `EXITO` as a substring of the success token.
- **Investigation loop terminates only when LLM outputs literal `COMPLETO` (uppercase)** and CitationAgent does NOT output `[VERIFICACION_FALLIDA]` or `[FALTA_FUENTE]`. Small wording changes to these prompts will break loop termination.
