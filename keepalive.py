"""
Keepalive. Runs on a schedule (GitHub Actions cron). No code, no phone.

It restores the saved session and performs light, real activity so Telegram
never counts the account as inactive. Reads config from environment secrets.
"""

import asyncio
import os
import sys
import traceback
import urllib.request
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.sessions import StringSession


def ping(suffix: str = "", body: str = "") -> None:
    """Ping the dead-man's switch (healthchecks.io), if one is configured.

    The point is the *absence* of a success ping: if this job stops running at all
    — Actions disabled, repo gone, cron silently dropped — nothing arrives and the
    monitor alerts. That failure mode is invisible to GitHub's own notifications.

    Never raises. A monitoring outage must not take down the keepalive itself.
    """
    url = os.environ.get("HEALTHCHECK_URL")
    if not url:
        return
    try:
        request = urllib.request.Request(
            url.rstrip("/") + suffix,
            data=body.encode("utf-8", "replace")[:10_000] or None,
        )
        with urllib.request.urlopen(request, timeout=10):
            pass
    except Exception as exc:
        print(f"warning: healthcheck ping failed ({exc}) — keepalive itself was fine.")


async def main() -> None:
    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    session_string = os.environ.get("TG_SESSION_STRING")

    missing = [
        name
        for name, val in (
            ("TG_API_ID", api_id),
            ("TG_API_HASH", api_hash),
            ("TG_SESSION_STRING", session_string),
        )
        if not val
    ]
    if missing:
        sys.exit(f"Missing required secrets: {', '.join(missing)}")

    # connect() rather than start(): start() would prompt for a phone number if the
    # session were dead, which hangs forever on a CI runner. connect() just fails.
    client = TelegramClient(StringSession(session_string), int(api_id), api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            sys.exit(
                "Session is not authorized — it was revoked or expired. "
                "Re-run login.py locally and update TG_SESSION_STRING."
            )

        me = await client.get_me()

        # Light, genuine activity: fetch identity + touch the dialog list.
        # Both are ordinary reads that register the account as active.
        dialog_count = 0
        async for _ in client.iter_dialogs(limit=1):
            dialog_count += 1
    finally:
        await client.disconnect()

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(
        f"[{now}] keepalive OK — @{me.username or me.id} "
        f"authorized, dialogs reachable ({dialog_count} sampled)."
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit as exc:
        # sys.exit("...") for a revoked session or missing secrets — report the reason.
        if exc.code:
            ping("/fail", str(exc.code))
        raise
    except BaseException:
        ping("/fail", traceback.format_exc())
        raise
    ping()
