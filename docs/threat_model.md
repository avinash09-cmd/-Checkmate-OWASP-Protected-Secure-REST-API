# Checkmate — Threat Model (STRIDE)

## 1. System overview

Checkmate is a task-management REST API. Users register, log in, and manage
their own tasks. Admins can view all users and audit logs.

**Assets to protect**
- User credentials (passwords, JWTs)
- User task data (confidentiality + integrity)
- Audit logs (integrity — must reflect what actually happened)
- Availability of the API itself

**Trust boundaries**
- Client (untrusted) → API (trust boundary 1: all input here is untrusted)
- API → Database (trust boundary 2: only the API should talk to the DB)

## 2. Data flow (simplified)

```
Client --(HTTPS)--> [API: middleware -> auth -> router -> service -> ORM] --> MySQL
```

## 3. STRIDE analysis

| Threat | Example | Mitigation in Checkmate |
|---|---|---|
| **S**poofing | Attacker pretends to be another user | Password hashing (Argon2), JWT signature verification, no session fixation |
| **T**ampering | Attacker modifies JWT claims to claim admin role | JWT signature verification with pinned algorithm (HS256 only, `alg: none` rejected) |
| **R**epudiation | User denies performing an action | Audit log records login attempts, task deletions, with timestamps |
| **I**nformation Disclosure | Attacker reads another user's tasks (IDOR) | Ownership check (`owner_id == current_user.id`) on every task query; password_hash never serialized in responses |
| **D**enial of Service | Attacker floods the login endpoint | Rate limiting on `/auth/login` (5/minute per IP by default) |
| **E**levation of Privilege | Normal user accesses `/admin/*` | RBAC dependency (`require_admin`) enforced server-side on every admin route; extra fields like `role` rejected on registration input |

## 4. Out of scope for this project (noted, not solved)

- Refresh token rotation / token revocation list (access tokens are short-lived, 15 min, as a mitigation)
- Multi-factor authentication
- Web Application Firewall / network-layer DDoS protection
- Full secrets management (e.g. Vault) — this project uses `.env` for local dev only

## 5. How this was validated

- Manual testing: attempted IDOR, SQL injection, JWT tampering, `alg: none` attack — see `tests/`
- Automated: Bandit (SAST), pip-audit (dependency scan), pytest security test suite
- See `docs/security_report.md` for scan results and findings
