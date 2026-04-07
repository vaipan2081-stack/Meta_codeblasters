# Hosted Validation Checklist

Use this as the final gate before submission.

## A. Build and boot

- [ ] Docker image builds successfully
- [ ] Service boots without runtime errors
- [ ] `/health` returns `200`

## B. API contract

- [ ] `GET /tasks` returns expected three task IDs
- [ ] `POST /reset` accepts valid task_id and optional seed
- [ ] `POST /step` returns `observation`, `reward`, `done`, `info`
- [ ] `GET /state` reflects current episode state
- [ ] `POST /grader` returns score object in [0, 1]

## C. Determinism

- [ ] Same seed + same action sequence gives same final score
- [ ] No random drift in repeated grading

## D. Inference compatibility

- [ ] `inference.py` runs against hosted endpoint
- [ ] Logs include `[START]`, `[STEP]`, `[END]` in correct order
- [ ] No malformed action crashes

## E. Submission evidence to archive

- [ ] Hosted URL
- [ ] Smoke test output
- [ ] Inference run logs
- [ ] One baseline run output
- [ ] Final score table (task1/task2/task3)

## F. Owner status

- [ ] Tushya local completion confirmed
- [ ] Shivansh hosted deployment evidence attached
- [ ] Final submit command and link verified
