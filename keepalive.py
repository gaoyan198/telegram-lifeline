"""
Keepalive. Runs on a schedule (GitHub Actions cron). No code, no phone.

It restores the saved session and performs light, real activity so Telegram
never counts the account as inactive. Reads config from environment secrets.
"""

import os
import sys
from datetime import datetime, timezone

from telethon.sync import TelegramClient
from telethon.sessions import StringSession


def main() -> None:
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

    with TelegramClient(StringSession(session_string), int(api_id), api_hash) as client:
        if not client.is_user_authorized():
            sys.exit(
                "Session is not authorized — it was revoked or expired. "
                "Re-run login.py locally and update TG_SESSION_STRING."
            )

        me = client.get_me()

        # Light, genuine activity: fetch identity + touch the dialog list.
        # Both are ordinary reads that register the account as active.
        dialog_count = sum(1 for _ in client.iter_dialogs(limit=1))

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(
            f"[{now}] keepalive OK — @{me.username or me.id} "
            f"authorized, dialogs reachable ({dialog_count} sampled)."
        )


if __name__ == "__main__":
    main()
