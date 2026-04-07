# Architecture Guide: What We Are Building, Why, and How It Works

## Executive Summary

This project is a **simulation environment + evaluation harness** for a hackathon where an AI policy must make decisions step-by-step and get scored.

In plain words:
- We built a Python web service that behaves like a "game engine" for decision-making episodes.
- A model (LLM or any policy) interacts with this engine one step at a time through APIs.
- Each step returns feedback (`reward`, `done`, and context), and final performance is scored by a grader.
- We added tests to ensure this is deterministic and reliable for judging.

Why this is useful for the hackathon:
- Judges need a standard way to run everyone’s environment.
- Results must be reproducible (same seed -> same behavior).
- The pipeline must be deployable (Docker/HF Spaces) and easy to evaluate.

---

## 1) Beginner-Friendly Overview (for a 2nd year CS student)

If you know Python fundamentals, think of this project as three layers:

1. **Environment layer (the world):**
  A backend service that holds state and rules. You send an action, it updates state, returns next observation + reward.

2. **Policy layer (the brain):**
  A script (`inference.py`) that decides what action to take based on current observation. This can be OpenAI, Gemini, HF model, local model, or even rule-based logic.

3. **Evaluation layer (the teacher):**
  Scripts (`smoke_test.py`, `baseline.py`, grader flow) that check API correctness, determinism, and performance.

### What is OpenEnv?

OpenEnv is a common interface pattern for environments where an agent interacts in episodes:
- `reset` starts a new episode and returns initial observation.
- `step` applies one action and returns next observation + reward + done.
- `done` tells you if episode is finished.

This is similar to reinforcement learning interfaces (Gym-style thinking), but adapted to the hackathon evaluator contract.

---

## 2) Problem Statement (what challenge this solves)

The hackathon expects a submission that is not just a model, but a **runnable system**:
- It must expose a clear API contract.
- It must be deterministic and reproducible.
- It must support automated judging in hosted infrastructure.

If we only gave raw model code, evaluation would be fragile and inconsistent.
So we built a structured environment service + runner + tests to make judging robust.

---

## 3) What Exactly We Built

### A. Environment service (`app/`)

Implemented with FastAPI. Core responsibilities:
- Manage episode lifecycle.
- Generate deterministic scenarios from seeds.
- Apply step transitions.
- Compute rewards and terminal conditions.
- Expose standard HTTP endpoints for external clients.

Important files:
- `app/main.py`: API routes and server wiring.
- `app/environment.py`: state transition logic, reward logic, scenario progression.
- `app/models.py`: request/response schemas including `StepResult`.

### B. Step contract standardization

We standardized `/step` to return a single envelope:

```json
{
  "observation": {...},
  "reward": 0.0,
  "done": false,
  "info": {...}
}
```

Why this matters:
- Every client script gets the same predictable structure.
- No hidden assumptions across scripts.
- Easier debugging, scoring, and compatibility.

### C. Model-policy runner (`inference.py`)

`inference.py` is the bridge between model and environment:
- Reads observation from environment.
- Calls model API (or local adapter) to decide next action.
- Sends action back to `/step`.
- Logs standardized run events (`[START]`, `[STEP]`, `[END]`) so evaluator can parse behavior.

### D. Validation and baseline tooling

- `smoke_test.py`: API shape checks + deterministic replay checks.
- `baseline.py`: reference policy score for sanity comparison.

### E. Deployment artifacts

- `Dockerfile`: containerized run.
- `openenv.yaml`: environment metadata/config expected by tooling.
- `README.md`: run instructions.

---

## 4) End-to-End Runtime Flow

### Flow A: Environment-only local validation (no model key needed)

1. Start server.
2. Call `reset` to get initial observation.
3. Send predefined/simple actions with `step`.
4. Verify returned fields and deterministic outcomes.

Used by `smoke_test.py` and `baseline.py`.

### Flow B: Full model-driven run

1. Start server.
2. Start `inference.py`.
3. For each step:
  - Fetch current observation.
  - Ask model for next action.
  - Post action to `/step`.
  - Receive `reward`, `done`, `info`.
4. Stop when `done=true`, emit final logs.

### Flow C: Hosted evaluation

1. Deploy service via Docker (HF Spaces).
2. Configure secrets/env vars.
3. Evaluator runs episodes with fixed seeds.
4. Grader computes comparable scores.

---

## 5) Why This Solution Is Unique / Strong

This submission is not just "call an LLM and hope". It is engineered for judge reliability:

1. **Evaluator-first architecture**
  Clean contract and logs designed for automated grading.

2. **Determinism as a first-class requirement**
  We explicitly validate seed reproducibility, which many teams skip.

3. **Provider-agnostic policy interface**
  OpenAI is not hardcoded. Gemini/HF/local policies can be plugged in with minimal changes.

4. **Separation of concerns**
  Environment logic is isolated from model API logic, making debugging and replacement easy.

5. **Submission readiness**
  Includes docs, metadata, Docker path, smoke tests, and baseline references.

---

## 6) Why We Chose This Architecture

### Choice 1: FastAPI service
- Easy to expose clean REST endpoints.
- Strong typing with Pydantic models.
- Works well with hosted container runtimes.

### Choice 2: StepResult envelope
- One response object with all state transition outputs.
- Reduces mismatch between clients and server.

### Choice 3: Separate `inference.py`
- Keeps model provider logic outside environment core.
- Lets us swap OpenAI/Gemini/local without rewriting server.

### Choice 4: Determinism checks in test flow
- Critical for fair hackathon judging.
- Prevents hidden randomness causing score variance.

---

## 7) OpenAI Key, Gemini, and Rule Compliance

### Do you need OpenAI key to test locally?
- **No** for environment tests (`smoke_test.py`, `baseline.py`).
- **Yes** only for full `inference.py` runs if your inference adapter uses OpenAI API.

### Is OpenAI mandatory?
- No. The runner is provider-agnostic.
- Gemini or another provider is also possible.

### Is API usage allowed in hackathon?
- Depends on official rules.
- If rules restrict external APIs, use local model or deterministic policy.

---

## 8) Mental Model: Think in Inputs and Outputs

At each timestep `t`:
- Input: `observation_t`
- Policy computes: `action_t`
- Environment returns: `observation_{t+1}, reward_t, done_t, info_t`

Episode score is generally accumulated from rewards:

$$
R = \sum_{t=0}^{T-1} reward_t
$$

Determinism means: same seed + same action sequence -> same trajectory and score.

---

## 9) Quick Start Commands

Start server:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 7860
```

Run environment checks:

```bash
python smoke_test.py
python baseline.py
```

Run inference (example with OpenAI):

```powershell
$env:OPENAI_API_KEY="sk-..."
python inference.py
```

---

## 10) Current Project Status

Completed:
- Feature-wise commits split by concern.
- `/step` contract upgraded to structured envelope.
- Inference runner added.
- Baseline/smoke tests aligned to new contract.
- Documentation and metadata prepared.

Pending:
- Push latest commits after final review.
- Hosted deployment and hosted smoke run.
- Final submission packaging.

---

## 11) If You Need to Explain This in 20 Seconds (Pitch)

"We built a deterministic OpenEnv-compatible decision environment with a clean step API, provider-agnostic inference runner, and reproducibility-focused test harness. It is engineered for reliable automated hackathon evaluation and deployable via Docker/HF Spaces."

