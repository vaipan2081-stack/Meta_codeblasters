# Judge Runbook

This document explains exactly how to run and validate this submission.

## 1) What you are running

This repo contains:
- OpenEnv-compatible incident triage environment API (FastAPI)
- `inference.py` runner (model-driven, emits `[START]/[STEP]/[END]` logs)
- `app_ui.py` Gradio human-review UI (optional)
- `smoke_test.py` and `baseline.py` for local validation

## 2) Local environment-only validation (no model key required)

```bash
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --host 127.0.0.1 --port 7860
```

In a second terminal:

```bash
py smoke_test.py --api-url http://127.0.0.1:7860
py baseline.py --task task1_easy --api-url http://127.0.0.1:7860
```

Expected:
- `/health` returns 200
- `smoke_test.py` passes contract checks and determinism checks
- `baseline.py` completes episodes and prints score breakdown

## 3) Inference runner (model-driven)

Set environment variables:

```powershell
$env:ENV_URL="http://127.0.0.1:7860"
$env:API_BASE_URL="https://your-model-endpoint/v1"
$env:MODEL_NAME="your-model"
$env:HF_TOKEN="your-token"
# Optional fallback
$env:OPENAI_API_KEY="sk-..."
```

Run:

```bash
py inference.py
```

Expected output pattern:
- One `[START]` line
- Multiple `[STEP]` lines
- One `[END]` line with final score/summary

## 4) Optional human demo UI (Gradio)

```powershell
$env:ENV_URL="http://127.0.0.1:7860"
py app_ui.py
```

Open: `http://127.0.0.1:7861`

Capabilities:
- Reset task with optional seed
- Execute action with JSON parameters
- Inspect state
- Grade episode
- Refresh task metadata

## 5) Hosted validation checklist

1. Deploy container to Hugging Face Space (Docker SDK)
2. Set secrets (`HF_TOKEN` / `OPENAI_API_KEY` if inference is model-backed)
3. Verify public `/health` = 200
4. Verify `/reset` and one `/step` call from public URL
5. Run smoke test against hosted URL
6. Run one full inference episode and archive logs
7. Record hosted URL and validation outputs in submission artifact

## 6) Notes on providers

- OpenAI is not mandatory; runner is provider-agnostic via env vars.
- Gemini/HF/local model adapters can be used if they match request/response behavior expected by `inference.py`.
- If hackathon rules disallow external API calls, use a local model policy and keep deterministic settings.
