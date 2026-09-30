import asyncio
import os

import pytest

from richgram import rich_button, rich_button_row, rich_heading, rich_kv_table, rich_send

NEEDED = ("API_ID", "API_HASH", "BOT_TOKEN", "CHAT_ID")


def test_live_rich_message_is_delivered():
    if not all(key in os.environ for key in NEEDED):
        pytest.skip("set API_ID, API_HASH, BOT_TOKEN and CHAT_ID to run the live test")

    from pyrogram import Client

    async def run():
        app = Client(
            "richgram_live_test",
            api_id=int(os.environ["API_ID"]),
            api_hash=os.environ["API_HASH"],
            bot_token=os.environ["BOT_TOKEN"],
            in_memory=True,
        )
        async with app:
            text = rich_heading("richgram live test", level=3) + rich_kv_table([("Status", "ok")])
            keyboard = rich_button_row(
                rich_button("Support", url="https://t.me/BadmundaXd", style="primary"),
                rich_button("Ping", callback_data="ping", style="success"),
            )
            return await rich_send(app, int(os.environ["CHAT_ID"]), text + keyboard)

    message = asyncio.run(run())
    assert message is not None
    assert message.id
  
