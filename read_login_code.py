"""
Fetch the login code Telegram just sent you — without a SIM or a second phone.

When you authorize a NEW official Telegram app, Telegram's servers issue a 5-digit
code. That is their protocol and nothing can skip it. But the code is delivered as
a *message to your own account* (from the service account 777000), and your session
string is a logged-in session, so it can simply read that message.

Net effect: your phone and SIM are never involved. The code becomes an internal
handshake this script handles for you.

Usage:
    export TG_API_ID=... TG_API_HASH=...

    # 1. On the new device, start the login and enter your phone number.
    # 2. Then run:
    .venv/bin/python read_login_code.py --watch

    # 3. Type the printed code into the new device, then your 2FA password.

--watch waits for a code that arrives AFTER the script starts, so you never paste a
stale one from an earlier login. Without it, the most recent code is printed.
"""

import argparse
import asyncio
import getpass
import os
import re
import sys
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.sessions import StringSession

# Telegram's official service account. Login codes always come from here.
TELEGRAM_SERVICE_ID = 777000

# Codes are 5 digits, often rendered as "Login code: 12345" or with spaces/dashes
# in some clients. Strip separators before matching so all variants work.
CODE_PATTERN = re.compile(r"\b(\d{5})\b")


def extract_code(text: str) -> str | None:
    if not text:
        return None
    # "1 2 3 4 5" and "12-345" both appear in the wild; normalise first.
    normalised = re.sub(r"(?<=\d)[\s\-](?=\d)", "", text)
    match = CODE_PATTERN.search(normalised)
    return match.group(1) if match else None


def describe_age(when: datetime) -> str:
    seconds = int((datetime.now(timezone.utc) - when).total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m ago"


async def newest_code(client, after: datetime | None):
    """Return (code, timestamp) for the most recent login code, or (None, None)."""
    async for message in client.iter_messages(TELEGRAM_SERVICE_ID, limit=10):
        if after is not None and message.date <= after:
            continue
        code = extract_code(message.message or "")
        if code:
            return code, message.date
    return None, None


async def main() -> None:
    parser = argparse.ArgumentParser(description="Read your Telegram login code.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="wait for a code that arrives after this script starts",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="seconds to wait in --watch mode (default: 180)",
    )
    args = parser.parse_args()

    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    if not api_id or not api_hash:
        sys.exit("Set TG_API_ID and TG_API_HASH first (see https://my.telegram.org).")

    session_string = (os.environ.get("TG_SESSION_STRING") or "").strip()
    if not session_string:
        try:
            session_string = getpass.getpass("Paste session string (input hidden): ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nNo session string entered.")
    if not session_string:
        sys.exit("No session string given — nothing to read the code with.")

    try:
        session = StringSession(session_string)
    except Exception:
        sys.exit(
            "That doesn't parse as a session string. It usually starts with '1' and "
            "runs to ~350 characters — check you copied the whole thing."
        )

    client = TelegramClient(session, int(api_id), api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            sys.exit(
                "That session string is not authorized — it was revoked or is stale. "
                "Without a live session there is no way to read the code; you would "
                "need SMS on the original number."
            )

        if not args.watch:
            code, when = await newest_code(client, after=None)
            if not code:
                sys.exit(
                    "No login code found in your recent Telegram service messages. "
                    "Start the login on the new device first, then run with --watch."
                )
            print(f"\n  Login code: {code}   (sent {describe_age(when)})\n")
            if (datetime.now(timezone.utc) - when).total_seconds() > 300:
                print("  Warning: that code is over 5 minutes old and probably expired.")
                print("  Re-request it on the new device, then run with --watch.\n")
            return

        started = datetime.now(timezone.utc)
        print(
            f"Waiting up to {args.timeout}s for a new login code...\n"
            "Trigger the login on the new device now (enter your phone number)."
        )
        deadline = asyncio.get_running_loop().time() + args.timeout
        while asyncio.get_running_loop().time() < deadline:
            code, when = await newest_code(client, after=started)
            if code:
                print(f"\n  Login code: {code}   (just arrived)\n")
                return
            await asyncio.sleep(3)

        sys.exit(
            f"\nNo new code arrived within {args.timeout}s. Check you entered the right "
            "phone number on the new device, and that it actually requested a code."
        )
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
