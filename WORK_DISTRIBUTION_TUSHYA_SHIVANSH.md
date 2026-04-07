# Work Distribution - Tushya and Shivansh

Last updated: 2026-04-07 (post-implementation update)
Context: Vaibhav is excluded from active execution load for this phase.

Update note (2026-04-08): Gradio UI ownership explicitly tracked and accelerated completion updates added.

## Principles used for fair split
- Work is split by independent tracks so both can run in parallel with minimal blocking.
- Tushya owns more of the total workload, especially code-critical and optimization-heavy tasks.
- Shivansh owns deployment, validation operations, and documentation packaging to avoid idle time.
- Blocking dependencies are explicitly minimized and listed.

## Ownership summary
- Tushya: Core code compliance, inference flow, API contract alignment, performance/readiness hardening.
- Shivansh: Hosting/deployment pipeline, submission artifacts, verification runs, and release packaging.

## Tushya - Primary implementation track (larger share)

### A. Submission-critical code
- [x] Implement root inference.py with strict hackathon logging format
  - Must emit [START], [STEP], [END] exactly.
  - Must use OpenAI client.
  - Must read API_BASE_URL, MODEL_NAME, HF_TOKEN (plus OPENAI_API_KEY fallback path if needed).
- [x] Align step/reset/state behavior to validator expectations
  - Ensure step response carries observation plus done/reward semantics expected by evaluator.
- [x] Ensure deterministic behavior in scenario selection and grading
  - Same seed and same actions must produce identical results.
- [x] Add explicit error handling for malformed actions and invalid task ids.
  - Implemented in existing API/env flow (invalid task id on reset and malformed action handling in step).

### B. Optimization and code quality (early, not deferred)
- [x] Optimize runtime path early
  - Keep responses compact and deterministic.
  - Prevent expensive unnecessary loops in baseline/inference flow.
- [x] Remove avoidable code-path ambiguity
  - Standardize response schema handling in baseline + inference scripts.
- [x] Add or improve reproducibility controls
  - Seed wiring for scenarios and scripts.
  - Stable model settings for repeatability.

### C. Test hardening
- [x] Upgrade smoke_test.py to include submission-specific checks
  - Schema checks for required fields.
  - Determinism rerun check.
  - Reward bounds and timeout handling.
- [x] Validate no regressions after API alignment
  - Baseline and smoke tests must both run cleanly.
  - Local smoke test status: 43/43 passed.

### D. Final engineering polish
- [x] Final code hygiene pass on changed files
  - Remove dead imports/unused paths.
  - Keep code readable and concise.
- [x] Prepare non-committed patch set for review (do not self-commit without your review).
  - Note: only the distribution doc commit was pushed earlier; implementation patches remain uncommitted.

## Shivansh - Parallel deployment and submission track

### A. Deployment track (can run while Tushya codes)
- [ ] Build and run Docker image locally
  - Confirm health endpoint and reset endpoint behavior.
- [ ] Set up/verify Hugging Face Space deployment
  - Confirm runtime boots and endpoint ping works.
- [ ] Validate hosted reset/step/state/grader flow from public URL.
- [ ] Build Gradio UI for Phase-3 human review (`app_ui.py`) and verify HF compatibility.

### B. Validation operations
- [ ] Run official pre-validation script against current branch
  - Capture output and failures.
- [ ] Re-run validation after Tushya patches are merged/reviewed.
- [ ] Record evidence logs for submission package.

### C. Submission packaging
- [ ] Prepare submission checklist artifact (single source of truth)
  - Commands, links, env vars, expected outputs.
- [ ] Update README submission sections
  - Setup, run, docker, hosted URL checks, inference run instructions.
- [ ] Assemble final artifact bundle
  - Repo link, HF Space link, validation output, score logs.

## Shared but non-blocking coordination rules
- [x] Only sync on interface contracts, not implementation details.
- [x] Tushya publishes API/inference contract changes in one short changelog note.
- [ ] Shivansh consumes that changelog and reruns validation/deployment without waiting for deep handoff.

## Changelog Note for Shivansh (consume first)
- /step response is now structured as: observation + reward + done + info.
- baseline.py and smoke_test.py already updated to this schema.
- inference.py added at repo root and now uses:
  - API_BASE_URL for model endpoint
  - MODEL_NAME for model id
  - HF_TOKEN (or OPENAI_API_KEY fallback) for API key
  - ENV_URL for environment endpoint (defaults to local 7860)
- openenv.yaml updated with inference metadata and required/optional env vars.

## Coordination / Dependency Alerts (avoid surprises)
- Shivansh must pull latest main before doing Docker/HF checks, else demo can fail due to old /step schema assumptions.
- Shivansh should not rely on previous /step raw observation contract in any scripts.
- Tushya must share exact ENV_URL used for hosted test before final validation run.
- Shivansh must report hosted endpoint links back in the checklist artifact to avoid broken demo links on submit day.
- If Shivansh finds validator mismatch with openenv schema, he should send exact validator output back to Tushya for fast patching.
- Final submission should happen only after both agree on one canonical HF Space URL and one inference command snippet.

## What Tushya Is Waiting On from Shivansh
- Hosted HF Space URL after successful deploy.
- Docker validation evidence (build log + health/reset proof).
- Official pre-validation script output against hosted endpoint.
- Final submission checklist artifact with links and outputs.

## Accelerated completion by Tushya (ownership override due deadline)
- [x] Implement Gradio UI scaffold (`app_ui.py`) for human review flow.
- [x] Add Gradio runtime dependency to `requirements.txt`.
- [x] Add Gradio run instructions to `README.md`.
- [x] Add judge-facing runbook (`JUDGE.md`) and hosted validation checklist (`HOSTED_VALIDATION_CHECKLIST.md`).
- [ ] Docker runtime verification and hosted HF checks still pending (needs deploy infra access/evidence).

## Infra constraint noted on current machine
- Docker CLI is unavailable on this workstation (`docker` command not found), so local container verification cannot be executed here.
- Docker/HF validation remains assigned as deployment work until run on a machine with Docker/HF access.

## Minimal dependency map (to reduce blocking)
- Shivansh can start immediately on docker/hf/prevalidation with current branch.
- Tushya can implement code tasks immediately in parallel.
- Only one sync point required:
  - When Tushya finishes API + inference changes, Shivansh reruns full validation and hosted checks.

## Exit criteria
- Tushya track done when all implementation + smoke/baseline checks are passing locally and patch is ready for your review (uncommitted if you want).
- Shivansh track done when docker + HF + prevalidation + submission artifacts are complete and evidence is documented.

## Current status snapshot
- Tushya track: COMPLETED locally (code + tests), waiting on your review and Shivansh deployment/validation outputs.
- Shivansh track: IN PROGRESS (deployment, hosted validation, submission packaging).
- Deadline acceleration update: Tushya also completed Gradio UI + docs/dependency tasks from deployment track to reduce risk.
