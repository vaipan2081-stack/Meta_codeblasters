# Work Distribution - Tushya and Shivansh

Last updated: 2026-04-07
Context: Vaibhav is excluded from active execution load for this phase.

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
- [ ] Implement root inference.py with strict hackathon logging format
  - Must emit [START], [STEP], [END] exactly.
  - Must use OpenAI client.
  - Must read API_BASE_URL, MODEL_NAME, HF_TOKEN (plus OPENAI_API_KEY fallback path if needed).
- [ ] Align step/reset/state behavior to validator expectations
  - Ensure step response carries observation plus done/reward semantics expected by evaluator.
- [ ] Ensure deterministic behavior in scenario selection and grading
  - Same seed and same actions must produce identical results.
- [ ] Add explicit error handling for malformed actions and invalid task ids.

### B. Optimization and code quality (early, not deferred)
- [ ] Optimize runtime path early
  - Keep responses compact and deterministic.
  - Prevent expensive unnecessary loops in baseline/inference flow.
- [ ] Remove avoidable code-path ambiguity
  - Standardize response schema handling in baseline + inference scripts.
- [ ] Add or improve reproducibility controls
  - Seed wiring for scenarios and scripts.
  - Stable model settings for repeatability.

### C. Test hardening
- [ ] Upgrade smoke_test.py to include submission-specific checks
  - Schema checks for required fields.
  - Determinism rerun check.
  - Reward bounds and timeout handling.
- [ ] Validate no regressions after API alignment
  - Baseline and smoke tests must both run cleanly.

### D. Final engineering polish
- [ ] Final code hygiene pass on changed files
  - Remove dead imports/unused paths.
  - Keep code readable and concise.
- [ ] Prepare non-committed patch set for review (do not self-commit without your review).

## Shivansh - Parallel deployment and submission track

### A. Deployment track (can run while Tushya codes)
- [ ] Build and run Docker image locally
  - Confirm health endpoint and reset endpoint behavior.
- [ ] Set up/verify Hugging Face Space deployment
  - Confirm runtime boots and endpoint ping works.
- [ ] Validate hosted reset/step/state/grader flow from public URL.

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
- [ ] Only sync on interface contracts, not implementation details.
- [ ] Tushya publishes API/inference contract changes in one short changelog note.
- [ ] Shivansh consumes that changelog and reruns validation/deployment without waiting for deep handoff.

## Minimal dependency map (to reduce blocking)
- Shivansh can start immediately on docker/hf/prevalidation with current branch.
- Tushya can implement code tasks immediately in parallel.
- Only one sync point required:
  - When Tushya finishes API + inference changes, Shivansh reruns full validation and hosted checks.

## Exit criteria
- Tushya track done when all implementation + smoke/baseline checks are passing locally and patch is ready for your review (uncommitted if you want).
- Shivansh track done when docker + HF + prevalidation + submission artifacts are complete and evidence is documented.
