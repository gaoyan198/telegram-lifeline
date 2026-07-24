# PRD — Telegram Lifeline

A zero-cost system that keeps a single Telegram account **permanently logged in** and
**permanently active**, without ever needing a verification code or a physical phone.

---

## 1. Problem

I own a Telegram account that I log out of frequently. On logging back in:

- **Sometimes** Telegram demands an SMS/app verification code, sometimes it doesn't.
- The code is only reachable on a **backup phone** that is not always with me.

Two risks follow:

1. **Short-term lockout** — I can't log in when the backup phone isn't around.
2. **Permanent loss** — Telegram terminates accounts after **6 months of inactivity**.
   If the account goes quiet *and* I lose the backup phone, the account is gone forever
   (the phone number is the only recovery anchor).

## 2. Why the code appears "sometimes"

Telegram issues a login code **only for a new authorization** (a new device/session).
An **existing authorized session never needs a code**. The account can hold many
concurrent sessions. So the root fix is not "avoid the code" — it is:

> Create **one** authorized session, persist it, and reuse it forever.

## 3. Goals

| # | Goal | Success criteria |
|---|------|------------------|
| G1 | Log in with no verification code | A saved session logs in on any machine, no SMS/app code |
| G2 | Never hit the 6-month inactivity cutoff | Automated activity at least every 30 days |
| G3 | Survive loss of the backup phone | Session + 2FA password + recovery email decouple access from the SIM |
| G4 | Cost = $0 | Runs on a free tier only |
| G5 | No server to babysit | No VPS, no always-on machine |

## 4. Non-goals

- Not a bot, scraper, spam, or mass-messaging tool. It touches **one** account — the owner's.
- Not multi-account. One account per deployment.
- Not a way to bypass another person's login. Owner-only.

## 5. Solution overview

Telegram's official client API exposes a **session string** — a portable credential that
represents one authorized login. Flow:

```
  ┌─────────────┐   one-time, with code   ┌──────────────────┐
  │  login.py   │ ─────────────────────▶  │  SESSION STRING  │
  │ (your PC)   │                          │  (secret, saved) │
  └─────────────┘                          └────────┬─────────┘
                                                     │ stored as encrypted secret
                                                     ▼
                              ┌──────────────────────────────────┐
                              │   GitHub Actions (free cron)      │
                              │   every 3 days: keepalive.py      │
                              │   → client.get_me() + read chats  │
                              │   → resets the inactivity timer   │
                              └──────────────────────────────────┘
```

- **G1** — the session string logs you in anywhere, no code. Import it in Telethon.
- **G2** — the scheduled job performs real API activity on a cadence far under 6 months.
- **G4/G5** — GitHub Actions scheduled workflows are free and require no server. The
  session string lives in an **encrypted repository secret**, never in the code.

### Why GitHub Actions (vs a cron on a VPS)

- Free minutes are ample: this job runs seconds, a few times a week.
- Secrets are encrypted at rest and injected only into the run.
- No uptime to manage; GitHub runs the schedule.

Alternatives that also fit "free": Oracle Cloud always-free VM + cron, Fly.io free
allowance, a Raspberry Pi at home. GitHub Actions is the least maintenance.

## 6. The permanence layer (surviving a lost phone) — do this once

The session alone keeps you *logged in*, but a session can still be revoked (e.g. you
hit "terminate all other sessions" by accident). Belt-and-suspenders:

1. **Set a 2FA / cloud password** (Settings → Privacy and Security → Two-Step
   Verification). This is what Telegram asks for on re-login *instead of* relying solely
   on the SMS code, and it is not tied to the SIM.
2. **Set a recovery email** on that 2FA password. Now account recovery no longer depends
   on the phone number.
3. **Keep the cloud session alive** (this repo). As long as one authorized session lives,
   you can spawn new ones from it and you never start from the SMS code.

With all three, losing the backup phone no longer means losing the account: the 2FA
password + recovery email recover it, and the live session keeps it from ever going idle.

## 7. Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Session string leaks | Full account access to whoever holds it | Store only as an encrypted secret; never commit; rotate by re-running `login.py` and revoking old sessions |
| GitHub changes free-tier | Job stops running | Failure notification (workflow emails owner on failure); portable to any cron host |
| Telegram revokes idle *sessions* (not just accounts) | Login lost | The keepalive activity keeps the session hot, not just the account |
| ToS | Account action | Owner-only, single account, low-frequency, no automation of messaging to others — ordinary API use |

## 8. Rollout

1. Run `login.py` locally once → obtain `SESSION_STRING` (enter code once, on any phone).
2. Set 2FA password + recovery email in the Telegram app.
3. Create a **private** GitHub repo, push this code.
4. Add secrets: `TG_API_ID`, `TG_API_HASH`, `TG_SESSION_STRING`.
5. Enable Actions. Confirm the first scheduled run succeeds.
6. Delete the local copy of the session string.

## 9. Open decisions

- **Cadence:** default every 3 days (well inside 6 months, cheap). Configurable.
- **Host:** GitHub Actions (recommended). Swap to Oracle/Fly/Pi with the same script.
