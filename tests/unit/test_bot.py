import importlib.util
import pathlib

from tests.helpers import FakeCallbackQuery, FakeMessage, rich_available

ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_bot():
    spec = importlib.util.spec_from_file_location("richgram_demo_bot", ROOT / "bot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bot = load_bot()


def test_home_text_has_the_demo_content():
    text = bot.home_text()
    assert "<h3>richgram demo</h3>" in text
    assert "<table" in text
    assert "<details>" in text


def test_home_keyboard_has_all_buttons_in_rows():
    kb = bot.home_kb()
    assert kb.count("<tg-button-row>") == 3
    for data in ("shuffle", "ping", "close"):
        assert f'data="{data}"' in kb
    assert 'url="https://t.me/BadmundaXd"' in kb


def test_close_button_is_always_red():
    for _ in range(20):
        kb = bot.home_kb()
        close = kb[kb.index('data="close"') - 60: kb.index('data="close"')]
        assert 'style="danger"' in close


def test_random_style_only_returns_known_styles():
    seen = {bot.random_style() for _ in range(200)}
    assert seen <= set(bot.STYLES)
    assert len(seen) > 1


async def test_start_replies_with_rich_message_and_buttons():
    message = FakeMessage()
    with rich_available(True):
        await bot.start(None, message)
    sent = message._client.last("send_rich_message")
    assert "richgram demo" in sent["rich_message"].html
    assert "<tg-button-row>" in sent["rich_message"].html
    assert sent["reply_parameters"].message_id == message.id


async def test_shuffle_edits_the_message_and_answers():
    cbq = FakeCallbackQuery(data="shuffle")
    with rich_available(True):
        await bot.shuffle(None, cbq)
    sent = cbq._client.last("edit_message_text")
    assert sent["message_id"] == cbq.message.id
    assert 'data="shuffle"' in sent["rich_message"].html
    assert cbq.answers == [("Colours shuffled", None)]


async def test_ping_shows_an_alert():
    cbq = FakeCallbackQuery(data="ping")
    await bot.ping(None, cbq)
    assert cbq.answers == [("Pong!", True)]
    assert cbq._client.calls == []


async def test_close_deletes_the_message():
    cbq = FakeCallbackQuery(data="close")
    await bot.close(None, cbq)
    assert cbq.message.deleted is True


async def test_start_still_answers_when_rich_is_unavailable():
    message = FakeMessage()
    with rich_available(False):
        await bot.start(None, message)
    sent = message._client.last("send_message")
    assert "richgram demo" in sent["text"]
    assert "<tg-button" not in sent["text"]
