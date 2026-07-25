"""
Route 1: get into your account using only the session string.

No login code. No SMS. No 2FA prompt. No phone. Authentication already happened
once, on your machine, and was frozen into the string — this just restores it.

Use this when you've lost the phone, the SIM, or every logged-in device, and you
need into the account right now from any computer.

Usage:
    export TG_API_ID=...
    export TG_API_HASH=...
    .venv/bin/python session_login.py

It asks for the session string with hidden input, so the string never lands in
your shell history. Paste it straight from your password manager. Alternatively
set TG_SESSION_STRING in the environment and it won't prompt.

    .venv/bin/python session_login.py --send "note to self"

sends a message to your own Saved Messages, which is a harmless way to prove
write access works, not just reads.
"""

import argparse
import asyncio
import getpass
import os
import sys

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--send",
        metavar="TEXT",
        help="send TEXT to your own Saved Messages, to confirm write access",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="how many recent chats to list (default: 10)",
    )
    args = parser.parse_args()

    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    if not api_id or not api_hash:
        sys.exit("Set TG_API_ID and TG_API_HASH first (see https://my.telegram.org).")

    session_string = (os.environ.get("TG_SESSION_STRING") or "").strip()
    if not session_string:
        # Hidden input: keeps a full-access credential out of shell history.
        try:
            session_string = getpass.getpass("Paste session string (input hidden): ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit("\nNo session string entered. Set TG_SESSION_STRING to skip the prompt.")
    if not session_string:
        sys.exit("No session string given — nothing to log in with.")

    # A truncated or mistyped paste should say so plainly rather than surfacing a
    # base64 traceback — this script gets used under pressure.
    try:
        session = StringSession(session_string)
    except Exception:
        sys.exit(
            "That doesn't parse as a session string. It usually starts with '1' and "
            "runs to ~350 characters — check you copied the whole thing."
        )

    # connect() rather than start(): start() would fall back to asking for a phone
    # number, which is the exact thing this script exists to avoid.
    client = TelegramClient(session, int(api_id), api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            sys.exit(
                "That session string is not authorized. It was revoked, or it is a "
                "stale copy. Re-run login.py from a device that can receive a code."
            )

        me = await client.get_me()
        print(f"\nLogged in as {me.first_name or ''} (@{me.username or me.id}) "
              f"id={me.id} — no code required.\n")

        if args.send:
            await client.send_message("me", args.send)
            print(f"Sent to Saved Messages: {args.send!r}\n")

        print(f"Most recent {args.limit} chats:")
        async for dialog in client.iter_dialogs(limit=args.limit):
            unread = f"  [{dialog.unread_count} unread]" if dialog.unread_count else ""
            print(f"  - {dialog.name}{unread}")
        print()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
