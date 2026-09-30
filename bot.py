import os
import random

from pyrogram import Client, filters

from richgram import (
    RICH_AVAILABLE,
    rich_button,
    rich_button_row,
    rich_details,
    rich_edit,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_reply,
)

STYLES = ("primary", "success", "danger")


def random_style() -> str:
    return random.choice(STYLES)


def home_text() -> str:
    return (
        rich_heading("richgram demo", level=3)
        + rich_note("Buttons change colour every time you tap Shuffle.")
        + rich_kv_table([
            ("Library", "richgram"),
            ("Rich support", "yes" if RICH_AVAILABLE else "no"),
        ])
        + rich_details("What is this?", "A test bot for the richgram package.")
    )


def home_kb() -> str:
    return (
        rich_button_row(
            rich_button("🎨 Shuffle colours", callback_data="shuffle", style=random_style()),
            rich_button("🏓 Ping", callback_data="ping", style=random_style()),
        )
        + rich_button_row(
            rich_button("🍬 Support", url="https://t.me/BadmundaXd", style=random_style()),
        )
        + rich_button_row(
            rich_button("⌯ Close ⌯", callback_data="close", style="danger"),
        )
    )


async def start(_, message):
    await rich_reply(message, home_text() + home_kb())


async def shuffle(_, cbq):
    await rich_edit(cbq, home_text() + home_kb())
    await cbq.answer("Colours shuffled")


async def ping(_, cbq):
    await cbq.answer("Pong!", show_alert=True)


async def close(_, cbq):
    await cbq.message.delete()


def create_app() -> Client:
    app = Client(
        "richgram_demo",
        api_id=int(os.getenv("API_ID", "0")),
        api_hash=os.getenv("API_HASH"),
        bot_token=os.getenv("BOT_TOKEN"),
        in_memory=True,
    )
    app.on_message(filters.command("start"))(start)
    app.on_callback_query(filters.regex("^shuffle$"))(shuffle)
    app.on_callback_query(filters.regex("^ping$"))(ping)
    app.on_callback_query(filters.regex("^close$"))(close)
    return app


if __name__ == "__main__":
    print("richgram demo bot started, press Ctrl+C to stop")
    create_app().run()
