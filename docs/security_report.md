# Checkmate — Security Report

Fill this in after you run Bandit, pip-audit, and OWASP ZAP against your local instance.
This is what turns the project from "I built an API" into "I built and validated a secure API" —
the part that stands out on a resume and in interviews.

## 1. Bandit (SAST) results

Run: `bandit -r app -ll`

| Finding | Severity | File | Status | Fix |
|---|---|---|---|---|
| (example) hardcoded_password_string | Medium | — | Fixed | Removed hardcoded test secret |

## 2. pip-audit (dependency scan) results

Run: `pip-audit -r requirements.txt`

| Package | CVE | Severity | Status | Fix |
|---|---|---|---|---|
| — | — | — | — | — |

## 3. OWASP ZAP (DAST) results

Run ZAP's baseline scan against your running local instance, e.g.:
`docker run -t zaproxy/zap-stable zap-baseline.py -t http://host.docker.internal:8000`

| Alert | Risk | Endpoint | Status | Fix |
|---|---|---|---|---|
| — | — | — | — | — |

## 4. Manual test results (pytest security suite)

Run: `pytest -v`

| Test | What it proves | Result |
|---|---|---|
| test_user_cannot_access_another_users_task | IDOR / Broken Access Control is blocked | Pass |
| test_normal_user_cannot_access_admin_routes | RBAC enforced | Pass |
| test_sql_injection_string_in_task_title_is_stored_safely | Injection blocked by ORM parameterization | Pass |
| test_alg_none_token_rejected | JWT algorithm confusion attack blocked | Pass |
| test_repeated_failed_logins_eventually_rate_limited | Brute-force mitigated | Pass |

## 5. Summary

- High-severity findings before fixes: ___
- High-severity findings after fixes: ___
- Key lessons learned: ___
