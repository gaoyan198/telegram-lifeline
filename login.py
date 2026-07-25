"""
One-time login. Run this ONCE on your own computer.

It authorizes a session (you enter the SMS/app code and, if set, your 2FA
password ONE time) and prints a SESSION STRING. That string is a full login
credential: from then on you never need a code again — you paste the string
into a secret and every future run reuses it.

Usage:
    pip install -r requirements.txt
    export TG_API_ID=...          # from https://my.telegram.org  -> API development tools
    export TG_API_HASH=...
    python login.py

Then copy the printed string into the GitHub secret TG_SESSION_STRING and
DELETE it from your machine / shell history.
"""

import asyncio
import os
import sys

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    if not api_id or not api_hash:
        sys.exit("Set TG_API_ID and TG_API_HASH first (see https://my.telegram.org).")

    async with TelegramClient(StringSession(), int(api_id), api_hash) as client:
        me = await client.get_me()
        session_string = client.session.save()
        print("\n" + "=" * 60)
        print(f"Logged in as: {me.first_name} (@{me.username})  id={me.id}")
        print("=" * 60)
        print("\nYour SESSION STRING (store as secret TG_SESSION_STRING):\n")
        print(session_string)
        print(
            "\nKeep this secret. Anyone with it controls the account.\n"
            "Store it in an encrypted secret only, then clear it from this machine.\n"
        )


if __name__ == "__main__":
    asyncio.run(main())
