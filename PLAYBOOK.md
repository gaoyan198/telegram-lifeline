# Playbook

What to do when you need back into the Telegram account. Written to be followed under
stress, in order, without thinking. Nothing here needs your SIM or your backup phone.

> **Keep a copy outside this repo.** If you ever lose GitHub access, the instructions
> would be locked in the same place as the thing they unlock. Save a copy in your
> password manager entry, or print it.

---

## What you need before any of this

Everything below assumes you can reach these three things. They should all live in your
password manager, in one entry:

| Item | What it is | Can it be recovered? |
|---|---|---|
| **Session string** | ~350 chars starting with `1`. Full account access. | **No.** The GitHub secret is write-only. If you lose your copy and every logged-in device, it's gone. |
| **2FA password** | The password you chose. Never sent to you. | Yes — via the recovery email on it. |
| **api_id / api_hash** | From <https://my.telegram.org> → API development tools | Yes — log back into that site and read them again. |

Setup once, on any computer:

```bash
gh repo clone gaoyan198/telegram-lifeline   # handles auth; no SSH key needed
cd telegram-lifeline
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export TG_API_ID=...        # from your password manager
export TG_API_HASH=...
```

Every command below assumes you've done this and are in that directory.

---

## Scenario A — "I need into my account right now"

No code, no SMS, no 2FA prompt, no phone. The session string *is* the completed
authentication.

```bash
.venv/bin/python session_login.py
```

Paste the session string at the hidden prompt. You get your identity and recent chats.
To confirm write access too:

```bash
.venv/bin/python session_login.py --send "test"
```

This is API access, not the official app UI. For the real app, go to Scenario B.

---

## Scenario B — "I want the Telegram app on a new phone, and I have no SIM"

Telegram always issues a 5-digit code when a new app authorizes — that is their protocol
and cannot be skipped. But the code is delivered as a **message to your own account**, and
your session string can read it. Your SIM is never involved.

1. Start the watcher on your computer:

   ```bash
   .venv/bin/python read_login_code.py --watch
   ```

2. On the new phone: install Telegram → **Start Messaging** → enter your phone number in
   full international format. (The *number* identifies the account. Nothing has to arrive
   on that line.)

3. The watcher prints the code within seconds.

4. Type the code into the phone, then your **2FA password** from your password manager.

5. You're in.

**On desktop instead?** Telegram Desktop's login screen has **"Log in by QR code"** — scan
it from any already-logged-in device and skip steps 2–4 entirely.

---

## Scenario C — "healthchecks.io emailed me" / the keepalive stopped

Check what broke:

```bash
gh run list -R gaoyan198/telegram-lifeline -w telegram-keepalive -L 5
gh run view -R gaoyan198/telegram-lifeline <run-id> --log-failed   # id from the list above
```

**If the log says the session is not authorized**, the session string was revoked — almost
always because someone hit *Terminate all other sessions* in the app. Mint a new one:

```bash
.venv/bin/python login.py                                    # needs a code — see Scenario B
gh secret set TG_SESSION_STRING -R gaoyan198/telegram-lifeline
gh workflow run telegram-keepalive -R gaoyan198/telegram-lifeline
```

**Save the new string to your password manager too** — the old copy is now dead.

**If GitHub disabled the workflow** (60 days of no repo activity — the heartbeat commit
should prevent this): open the Actions tab and click *Enable workflow*, then run it once.

---

## Scenario D — "I lost the phone, the SIM, and every logged-in device"

You are fine **if** you still have the session string. Go to Scenario A, then Scenario B to
get the app back on a new phone.

You are in trouble only if the session string is **also** gone. In that case SMS to your
original number is the only remaining route — which means recovering the number through
your carrier. This is the single failure mode the whole setup exists to prevent, and the
only defence is keeping that string somewhere you can always reach.

---

## Health check (takes 10 seconds)

Open [`last-run.txt`](last-run.txt) on GitHub. If the newest line is within ~3 days,
everything is working. Or:

```bash
gh run list -R gaoyan198/telegram-lifeline -w telegram-keepalive -L 5
```

Green runs every ~3 days = healthy. You should not need to check this — healthchecks.io
emails you if pings stop, and GitHub emails you if a run fails.

---

## Things that will break this

- **"Terminate all other sessions"** in the Telegram app. Kills the keepalive *and* your
  personal session string. Never press it unless you intend to re-mint both.
- **Deleting or renaming the GitHub repo**, or making it public (the secrets are
  full-access credentials).
- **Losing your Google account**, if that is the only place the session string lives — and
  note that Google account recovery often depends on the very phone you're trying to route
  around. Keep Google backup codes somewhere physical.
- **Letting Telegram Desktop log out everywhere.** Keeping one long-lived session on your
  laptop is a free second way to receive a login code.

---

## Command reference

| Command | Does what |
|---|---|
| `session_login.py` | Log in with the string. No code. |
| `session_login.py --send "x"` | Same, plus prove write access. |
| `read_login_code.py --watch` | Wait for and print the next login code. |
| `login.py` | Mint a **new** session string (needs a code). |
| `keepalive.py` | What CI runs every 3 days. |
| `gh workflow run telegram-keepalive -R gaoyan198/telegram-lifeline` | Force a keepalive run now. |
