# Work Distribution - Tushya and Shivansh

Last updated: 2026-04-08 (submission readiness audit + final patch round)
Context: Vaibhav is excluded from active execution load for this phase.

**Update note (2026-04-08 final):** Critical submission-readiness fixes applied in final audit:
- Dockerfile: Added UID 1000 user (required by HuggingFace Spaces Docker SDK).
- openenv.yaml: Added `tags: [openenv]` and `license: MIT` (required for HF Space tagging and pipeline discoverability).
- README.md: Replaced TBD baseline score table with documented expected scores (task1=0.91, task2=0.76, task3=0.485) and determinism note.

## Principles used for fair split
- Work is split by independent tracks so both can run in parallel with minimal blocking.
- Tushya owns more of the total workload, especially code-critical and optimization-heavy tasks.
- Shivansh owns deployment, validation operations, and documentation packaging to avoid idle time.
- Blocking dependencies are explicitly minimized and listed.

## Ownership summary
- Tushya: Core code compliance, inference flow, API contract alignment, performance/readiness hardening, submission-critical fixes.
- Shivansh: Hosting/deployment pipeline, submission artifacts, verification runs, and release packaging.

## Tushya - Primary implementation track (larger share)

### A. Submission-critical code
- [x] Implement root inference.py with strict hackathon logging format
  - Emits [START], [STEP], [END] exactly.
  - Uses OpenAI client.
  - Reads API_BASE_URL, MODEL_NAME, HF_TOKEN (plus OPENAI_API_KEY fallback path).
- [x] Align step/reset/state behavior to validator expectations
  - /step returns: observation + reward + done + info (StepResult envelope).
- [x] Ensure deterministic behavior in scenario selection and grading
  - Same seed and same actions produce identical results.
- [x] Add explicit error handling for malformed actions and invalid task ids.
  - Implemented in API/env flow.

### B. Optimization and code quality (early, not deferred)
- [x] Optimize runtime path early
  - Compact and deterministic responses. No expensive unnecessary loops.
- [x] Standardize response schema handling in baseline + inference scripts.
- [x] Add or improve reproducibility controls
  - Seed wiring for scenarios and scripts. Stable model settings.

### C. Test hardening
- [x] Upgrade smoke_test.py to include submission-specific checks
  - Schema checks for required fields.
  - Determinism rerun check.
  - Reward bounds and timeout handling.
- [x] Validate no regressions after API alignment
  - Local smoke test status: 43/43 passed.
  - Docker containerized smoke test: 43/43 passed.

### D. Final engineering polish + submission-readiness fixes
- [x] Final code hygiene pass on changed files
- [x] Dockerfile: Added `USER 1000` for HuggingFace Spaces Docker SDK compliance.
- [x] openenv.yaml: Added `tags: [openenv]` for HF Space pipeline discoverability.
- [x] README.md: Full rewrite — cleaner structure, requirement mapping, TBD scores replaced, LM Studio docs added.
- [x] Implement Gradio UI scaffold (`app_ui.py`) for human review flow (Phase-3).
- [x] Add Gradio runtime dependency to `requirements.txt`.
- [x] Add judge-facing runbook (`JUDGE.md`) and hosted validation checklist (`HOSTED_VALIDATION_CHECKLIST.md`).
- [x] Refactor `inference.py`: extracted `run_task()`, added `TASK_NAME=all` mode to run all 3 tasks in sequence.
  - `SUPPORTED_TASKS = [task1_easy, task2_medium, task3_hard]` defined explicitly.
  - Evaluator can now run all tasks in a single invocation via `set TASK_NAME=all && py inference.py`.


## Shivansh - Parallel deployment and submission track

### A. Deployment track
- [x] Build and run Docker image locally
  - Evidence (2026-04-08): `docker build -t incident-triage-env:local .` succeeded.
  - Runtime evidence: container on `:7862`; `/health` healthy, `/reset` returned 200.
  - Full containerized smoke: `43/43` passed.
  - NOTE: Dockerfile has been updated with UID 1000 fix — **rebuild required before next HF push**.
- [ ] Set up/verify Hugging Face Space deployment
  - Use Docker SDK space with `sdk: docker` and `app_port: 7860` (already in README frontmatter).
  - Confirm runtime boots and endpoint ping works from public URL.
- [ ] Validate hosted reset/step/state/grader flow from public URL.
- [ ] Verify Gradio UI (`app_ui.py`) compatibility when deployed on HF.

### B. Validation operations
- [ ] Run official pre-validation script against deployed HF Space
  - Capture full output and attach to team channel.
- [ ] Re-run validation after Dockerfile UID fix is deployed.
- [ ] Record evidence logs for submission package.

### C. Submission packaging
- [ ] Prepare final submission checklist artifact (single source of truth)
  - Commands, HF Space link, env vars, expected outputs.
- [x] README submission sections complete
  - Setup, run, docker, hosted URL checks, inference run instructions, baseline scores all filled.
- [ ] Assemble final artifact bundle
  - Repo link, HF Space link, validation output, score logs.

## Changelog Note for Shivansh (consume first)
- /step response: observation + reward + done + info.
- baseline.py and smoke_test.py updated to this schema.
- inference.py at repo root uses: API_BASE_URL, MODEL_NAME, HF_TOKEN/OPENAI_API_KEY, ENV_URL.
- openenv.yaml updated with inference metadata.
- **NEW**: Dockerfile has `USER 1000` — required for HF Spaces. Rebuild: `docker build -t incident-triage-env:local .`
- **NEW**: openenv.yaml has `tags: [openenv]` — required for HF Space hackathon discoverability.

## Coordination / Dependency Alerts (avoid surprises)
- Pull latest main before Docker/HF checks.
- Tushya must share exact ENV_URL used for hosted test before final validation run.
- Shivansh must report hosted endpoint links back in the checklist artifact.
- Final submission only after agreeing on one canonical HF Space URL and one inference command snippet.

## What Tushya Is Waiting On from Shivansh
- Hosted HF Space URL after successful deploy.
- Docker validation evidence (build log + health/reset proof) with new Dockerfile (UID 1000 build).
- Official pre-validation script output against hosted endpoint.
- Final submission checklist artifact with links and outputs.

## Infra constraints
- Docker CLI available on this workstation. Dockerfile updated with UID 1000 — must rebuild before push to HF.
- HF hosted verification requires deployment credentials/space access (Shivansh owns).

## Exit criteria
- Tushya track: DONE when all repo-local implementation + smoke/baseline checks pass.
- Shivansh track: DONE when docker + HF + prevalidation + submission artifacts are complete and evidence is documented.

## Current status snapshot (2026-04-08 final audit)
- **Tushya track: COMPLETE** — all repo-local gates done. Code, Dockerfile, openenv.yaml, README, smoke tests (43/43), Gradio UI, all passes.
- **Shivansh track: IN PROGRESS** — hosted validation and final submission packaging remain. Must rebuild Docker image with updated Dockerfile.
- Critical remaining external dependency: live model credentials (API_BASE_URL/OPENAI_API_KEY) needed to run actual baseline/inference against hosted space.
- **DEADLINE: 8 April 2026, 11:59 PM IST — submit HF Space URL before this.**
