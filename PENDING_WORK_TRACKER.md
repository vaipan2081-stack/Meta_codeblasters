# Meta AI Hackathon - Pending Work Tracker

Last updated: 2026-04-07
Scope used: repo code + Official Website Info + team WhatsApp notes + attached PDF plans.

## How to use this tracker
- Mark each item as done by changing [ ] to [x].
- Add owner initials in the Owner field.
- Keep notes short and factual in Notes.
- Do not merge to main unless all P0 items are complete.

## Snapshot (what is already present)
- FastAPI environment exists with reset/step/state/tasks/grader endpoints.
- 3 difficulty tasks exist (easy, medium, hard) with scenario data and grader logic.
- Dockerfile, openenv.yaml, baseline.py, smoke_test.py, README.md exist.

## P0 - Submission blockers (finish first)

- [ ] Create root inference.py exactly as required by hackathon format
  - Owner: 
  - Done criteria: script name is inference.py at repo root; uses OpenAI client; reads API_BASE_URL, MODEL_NAME, HF_TOKEN/OPENAI_API_KEY from env; emits strict [START], [STEP], [END] structured logs in required order.
  - Notes: official requirement explicitly says inference.py is mandatory; currently only baseline.py exists.

- [ ] Align API behavior with validator expectations for step/reset/state contract
  - Owner: 
  - Done criteria: step flow returns/contains observation + reward + done semantics expected by validator/inference flow; no schema mismatch in automated checks.
  - Notes: current /step returns observation object only, while official sample flow expects reward/done each step.

- [ ] Run official pre-validation script and fix all failing checks
  - Owner: 
  - Done criteria: all mandatory checks pass locally before submission (spec, docker, baseline/inference, 3 tasks+graders, ping/reset behavior).
  - Notes: attach final validation output to team chat.

- [ ] Ensure openenv.yaml matches exact required schema
  - Owner: 
  - Done criteria: openenv validate passes with no warnings/errors; task metadata, API metadata, and required fields are complete.
  - Notes: planning docs repeatedly flagged schema strictness as a major risk.

- [ ] Confirm deterministic grading and reproducibility
  - Owner: 
  - Done criteria: same task + seed + same diagnosis gives identical score; no random drift in graders.
  - Notes: add at least one deterministic regression check in smoke tests.

- [ ] Add and verify required environment variables for evaluation setup
  - Owner: 
  - Done criteria: API_BASE_URL, MODEL_NAME, HF_TOKEN (and OPENAI_API_KEY if required by code path) are documented and consumed correctly.
  - Notes: requirement is explicitly listed in official instructions.

## P1 - High-priority quality/compliance

- [ ] Update README to match final implementation and judging rubric
  - Owner: 
  - Done criteria: includes environment motivation, exact action/observation schema, task descriptions/difficulty, setup, docker run, baseline/inference commands, reproducible scores, and troubleshooting.
  - Notes: current README is good but not fully aligned to final submission checklist.

- [ ] Produce reproducible baseline report for all 3 tasks
  - Owner: 
  - Done criteria: fixed-seed run table with per-task and overall score, model/version noted, command included.
  - Notes: keep this in README and optionally a separate artifact.

- [ ] Harden smoke_test.py for submission reality
  - Owner: 
  - Done criteria: tests include schema checks, timeout behavior, invalid actions, grader range checks [0.0,1.0], and deterministic rerun check.
  - Notes: current smoke test is solid but should include deterministic check and submission-specific assertions.

- [ ] Verify docker runtime and performance limits
  - Owner: 
  - Done criteria: inference finishes under 20 minutes on constrained machine assumptions (2 vCPU, 8 GB RAM).
  - Notes: include timing evidence in notes.

- [ ] Hugging Face Space deployment dry run
  - Owner: 
  - Done criteria: space deploys, health returns 200, reset works from public URL, one full inference run succeeds.
  - Notes: tag/config as required by OpenEnv hackathon.

## P2 - Consistency and handoff cleanup

- [ ] Remove confusion between old ML-debugger planning docs and current incident-triage implementation
  - Owner: 
  - Done criteria: final README/submission docs mention only the shipped incident-triage environment; no contradictory task labels remain.
  - Notes: current context folder contains rough/legacy plan docs; keep as reference only.

- [ ] Add a single source-of-truth submission checklist file
  - Owner: 
  - Done criteria: one checklist with final commands, links, and acceptance criteria for submit day.
  - Notes: this tracker can be extended for that purpose.

- [ ] Final code hygiene pass
  - Owner: 
  - Done criteria: remove dead imports/unused code paths; pin dependency versions if needed for reproducibility; ensure clean startup logs.
  - Notes: do this after P0/P1 to avoid churn.

## Optional (if time remains)

- [ ] Add a lightweight human demo UI for Phase-3 review
  - Owner: 
  - Done criteria: simple UI can reset task, send actions, show observations, submit diagnosis, and show score.
  - Notes: not mandatory for validation, but useful for human judges.

- [ ] Add CI workflow for smoke test + docker build
  - Owner: 
  - Done criteria: PR check runs smoke tests and docker build at minimum.
  - Notes: helps avoid last-minute breakage.

## Team split suggestion (from current repo state)

- Member A: API/spec compliance + inference.py + validator pass
- Member B: grader determinism + smoke tests + baseline reproducibility report
- Member C: README + HF deployment + final submission checklist

## Submit-day final gate

- [ ] P0 all checked
- [ ] P1 all checked
- [ ] inference.py root file present and tested
- [ ] docker build and run verified
- [ ] HF URL reset ping verified
- [ ] final scores and logs archived in team chat
