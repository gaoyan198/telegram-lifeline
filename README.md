# .telegram-lifeline

Keep one Telegram account **logged in forever** (no verification code) and **never idle**
(never hit the 6-month termination) — for **free**, with **no server**.

See [PRD.md](PRD.md) for the full rationale. Quick version:

- **No more codes:** Telegram only asks for a code on a *new* login. Authorize once,
  export a **session string**, and reuse it forever — from any machine, no phone.
- **No termination:** a free GitHub Actions cron runs every 3 days and performs light
  activity, resetting the inactivity clock indefinitely.
- **Phone-loss proof:** set a 2FA password + recovery email once, so account recovery no
  longer depends on your SIM.

## Setup (≈10 minutes, once)

1. **Get API credentials** — go to <https://my.telegram.org> → *API development tools* →
   create an app. Note the `api_id` and `api_hash`.

2. **Install + authorize once** (on your own computer):
   ```bash
   pip install -r requirements.txt
   export TG_API_ID=123456
   export TG_API_HASH=abcdef...
   python login.py
   ```
   Enter the code (and 2FA password if set) **one time**. Copy the printed
   `SESSION STRING`.

3. **Harden the account** in the Telegram app (do this once):
   - Settings → Privacy & Security → **Two-Step Verification** → set a password.
   - Add a **recovery email** to that password.

4. **Create a PRIVATE GitHub repo** and push this folder. Keep it private — the workflow
   handles a full-access credential.

5. **Add repository secrets** (Settings → Secrets and variables → Actions):
   - `TG_API_ID`
   - `TG_API_HASH`
   - `TG_SESSION_STRING`

6. **Enable Actions.** Open the *Actions* tab → run **telegram-keepalive** manually once
   (`Run workflow`) to confirm it succeeds. After that it runs on schedule.

7. **Clean up:** delete the session string from your shell history / local files.

## To log in later without a code

Import the same `TG_SESSION_STRING` into any Telethon client — you're in, no code. To add
a fresh phone/desktop client, you can also generate new logins from the live session.

## Rotating / revoking

Lost control of the string, or want to reset? Re-run `login.py` to mint a new session,
update the secret, and in the Telegram app use *Settings → Devices* to terminate old
sessions.

## Cost

GitHub Actions scheduled workflows on a private repo run within the free monthly minutes;
this job takes seconds a few times a week. Effectively $0.

## Scope / ethics

Owner-only, single account. This does **not** message other people, scrape, or automate
anything beyond a lightweight liveness check on your own account. Don't use it for anything
else.
