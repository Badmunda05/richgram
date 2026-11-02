from types import SimpleNamespace

import pytest
from telethon import types as telethon_types
from telethon.errors import FloodWaitError

from richgram import rich_details, rich_emoji, rich_heading
from richgram import telethon as telethon_adapter
from richgram.telethon import (
    TELETHON_RICH_AVAILABLE,
    _resolve_message,
    telethon_block_details,
    telethon_block_paragraph,
    telethon_edit_request,
    telethon_input_rich,
    telethon_rich_edit,
    telethon_rich_reply,
    telethon_rich_send,
    telethon_rich_send_blocks,
    telethon_send_request,
)

RICH = rich_heading("Hi", level=3)
EMOJI_ID = "5368324170671202286"


class FakeTelethonClient:
    def __init__(self, fail=(), fail_error=None):
        self.calls = []
        self.fail = set(fail)
        self.fail_error = fail_error

    async def __call__(self, request):
        self.calls.append(("invoke", request))
        if "invoke" in self.fail:
            raise self.fail_error or RuntimeError("invoke failed")
        message = SimpleNamespace(id=4242)
        return SimpleNamespace(updates=[SimpleNamespace(message=message)])

    async def get_messages(self, entity, ids=None):
        self.calls.append(("get_messages", {"entity": entity, "ids": ids}))
        return SimpleNamespace(id=ids)

    async def send_message(self, entity, text, **kwargs):
        self.calls.append(("send_message", {"entity": entity, "text": text, **kwargs}))
        if "send_message" in self.fail:
            raise self.fail_error or RuntimeError("send_message failed")
        return SimpleNamespace(id=len(self.calls), call="send_message")

    async def edit_message(self, entity, message, text, **kwargs):
        self.calls.append(("edit_message", {
            "entity": entity, "message": message, "text": text, **kwargs,
        }))
        if "edit_message" in self.fail:
            raise self.fail_error or RuntimeError("edit_message failed")
        return SimpleNamespace(id=len(self.calls), call="edit_message")

    def names(self):
        return [name for name, _ in self.calls]

    def last(self, name=None):
        for call_name, kwargs in reversed(self.calls):
            if name is None or call_name == name:
                return kwargs
        return None


class FakeTelethonMessage:
    def __init__(self, client=None, chat_id=100, message_id=7):
        self._client = client or FakeTelethonClient()
        self.client = self._client
        self.chat_id = chat_id
        self.id = message_id


def test_telethon_rich_available_with_real_telethon():
    assert TELETHON_RICH_AVAILABLE is True


def test_input_rich_html_is_normalised():
    rich = telethon_input_rich("a\nb" + rich_heading("Hi", level=3))
    assert isinstance(rich, telethon_types.InputRichMessageHTML)
    assert rich.html == "a<br/>\nb<h3>Hi</h3>"


def test_input_rich_markdown():
    rich = telethon_input_rich("# Hi", markdown=True)
    assert isinstance(rich, telethon_types.InputRichMessageMarkdown)
    assert rich.markdown == "# Hi"


def test_input_rich_rejects_empty_text():
    with pytest.raises(ValueError, match="non-empty text"):
        telethon_input_rich("")


def test_input_rich_without_telethon_raises():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(telethon_adapter, "_load_telethon",
                   lambda: (_ for _ in ()).throw(RuntimeError("no telethon")))
        with pytest.raises(RuntimeError, match="no telethon"):
            telethon_input_rich("hi")


def test_send_request_carries_rich_message_and_companion_text():
    request = telethon_send_request(123, RICH, reply_to_msg_id=7, top_msg_id=9, silent=True)
    assert request.peer == 123
    assert request.message == "<h3>Hi</h3>"
    assert request.silent is True
    assert isinstance(request.rich_message, telethon_types.InputRichMessageHTML)
    assert request.rich_message.html == "<h3>Hi</h3>"
    assert request.reply_to.reply_to_msg_id == 7
    assert request.reply_to.top_msg_id == 9
    assert request.random_id is not None


def test_send_request_markdown_companion_is_the_source():
    request = telethon_send_request(123, "# Hi", markdown=True)
    assert isinstance(request.rich_message, telethon_types.InputRichMessageMarkdown)
    assert request.message == "# Hi"


def test_edit_request_carries_rich_message():
    request = telethon_edit_request(123, 42, rich_details("S", "B"))
    assert request.peer == 123
    assert request.id == 42
    assert request.message == "<details><summary>S</summary>B</details>"
    assert isinstance(request.rich_message, telethon_types.InputRichMessageHTML)


async def test_rich_send_invokes_raw_request():
    client = FakeTelethonClient()
    result = await telethon_rich_send(client, 123, RICH)
    assert client.names() == ["invoke"]
    request = client.last("invoke")
    assert request.peer == 123
    assert "<h3>Hi</h3>" in request.rich_message.html
    assert result.id == 4242


async def test_rich_send_plain_html_uses_send_message():
    client = FakeTelethonClient()
    await telethon_rich_send(client, 123, "<b>hello</b>")
    assert client.names() == ["send_message"]
    assert client.last()["text"] == "<b>hello</b>"
    assert client.last()["parse_mode"] == "html"


async def test_rich_send_falls_back_when_rich_fails():
    client = FakeTelethonClient(fail={"invoke"})
    result = await telethon_rich_send(client, 123, RICH)
    assert client.names() == ["invoke", "send_message"]
    assert "<b>Hi</b>" in client.last("send_message")["text"]
    assert result.call == "send_message"


async def test_rich_send_returns_none_when_everything_fails():
    client = FakeTelethonClient(fail={"invoke", "send_message"})
    assert await telethon_rich_send(client, 123, RICH) is None


async def test_rich_send_empty_text_sends_nothing():
    client = FakeTelethonClient()
    assert await telethon_rich_send(client, 123, "") is None
    assert client.calls == []


async def test_rich_send_plain_fallback_keeps_premium_emoji_tag():
    client = FakeTelethonClient(fail={"invoke"})
    await telethon_rich_send(client, 123, "Nice " + rich_emoji(EMOJI_ID, "🔥"))
    assert "tg-emoji" in client.last("send_message")["text"]
    from telethon.extensions.html import parse as parse_html

    text, entities = parse_html(client.last("send_message")["text"])
    assert text == "Nice 🔥"
    assert entities[0].document_id == int(EMOJI_ID)


async def test_rich_reply_replies_to_the_message():
    client = FakeTelethonClient()
    message = FakeTelethonMessage(client)
    await telethon_rich_reply(message, RICH)
    request = client.last("invoke")
    assert request.peer == 100
    assert request.reply_to.reply_to_msg_id == 7


async def test_rich_edit_via_message_target():
    client = FakeTelethonClient()
    message = FakeTelethonMessage(client)
    await telethon_rich_edit(message, RICH)
    request = client.last("invoke")
    assert request.peer == 100
    assert request.id == 7
    assert "<h3>Hi</h3>" in request.rich_message.html


async def test_rich_edit_via_client_and_ids_with_plain_fallback():
    client = FakeTelethonClient(fail={"invoke"})
    await telethon_rich_edit(client, RICH, chat=123, message_id=42)
    assert client.names() == ["invoke", "edit_message"]
    assert client.last("edit_message")["message"] == 42
    assert "<b>Hi</b>" in client.last("edit_message")["text"]


async def test_rich_edit_returns_none_without_target():
    assert await telethon_rich_edit(FakeTelethonClient(), RICH) is None


def test_block_paragraph_and_details():
    paragraph = telethon_block_paragraph("hello")
    assert isinstance(paragraph, telethon_types.PageBlockParagraph)
    assert paragraph.text == "hello"
    inner = telethon_block_details("Inner", [paragraph])
    assert isinstance(inner, telethon_types.PageBlockDetails)
    assert inner.title == "Inner"
    assert inner.open is None
    outer = telethon_block_details("Outer", [inner], open=True)
    assert outer.open is True
    assert outer.blocks[0] is inner


def test_block_details_validates_title():
    with pytest.raises(ValueError, match="non-empty title"):
        telethon_block_details("", [])


async def test_rich_send_blocks_invokes_with_page_blocks():
    client = FakeTelethonClient()
    blocks = [telethon_block_details("Guide", [telethon_block_paragraph("hi")])]
    result = await telethon_rich_send_blocks(client, 123, blocks)
    assert client.names() == ["invoke"]
    request = client.last("invoke")
    assert request.rich_message.blocks == blocks
    assert result.id == 4242


async def test_rich_send_blocks_empty_and_failed():
    client = FakeTelethonClient()
    assert await telethon_rich_send_blocks(client, 123, []) is None
    assert client.calls == []
    failing = FakeTelethonClient(fail={"invoke"})
    assert await telethon_rich_send_blocks(
        failing, 123, [telethon_block_paragraph("hi")]
    ) is None


def test_load_telethon_accepts_installed_build():
    types, functions = telethon_adapter._load_telethon()
    assert types.InputRichMessageHTML is not None
    assert functions.messages.SendMessageRequest is not None


def test_load_telethon_rejects_request_without_rich_message(monkeypatch):
    from telethon import functions as tl_functions

    class StubRequest:
        def __init__(self, peer, message):
            pass

    monkeypatch.setattr(tl_functions.messages, "SendMessageRequest", StubRequest)
    with pytest.raises(RuntimeError, match="rich_message"):
        telethon_adapter._load_telethon()


async def test_resolve_message_prefers_update_message():
    client = FakeTelethonClient()
    result = SimpleNamespace(updates=[SimpleNamespace(message=SimpleNamespace(id=7))])
    assert (await _resolve_message(client, 123, result)).id == 7
    assert client.calls == []


async def test_resolve_message_fetches_by_update_id():
    client = FakeTelethonClient()
    result = SimpleNamespace(updates=[SimpleNamespace(id=55)])
    assert (await _resolve_message(client, 123, result)).id == 55
    assert client.names() == ["get_messages"]


async def test_resolve_message_returns_none_when_unresolvable():
    client = FakeTelethonClient()
    assert await _resolve_message(client, 123, SimpleNamespace(updates=[])) is None
    assert await _resolve_message(client, 123, SimpleNamespace()) is None


async def test_rich_send_reraises_flood_wait_without_fallback():
    client = FakeTelethonClient(
        fail={"invoke"}, fail_error=FloodWaitError(None, 5)
    )
    with pytest.raises(FloodWaitError):
        await telethon_rich_send(client, 123, RICH)
    assert client.names() == ["invoke"]


async def test_rich_send_blocks_reraises_flood_wait():
    client = FakeTelethonClient(
        fail={"invoke"}, fail_error=FloodWaitError(None, 5)
    )
    with pytest.raises(FloodWaitError):
        await telethon_rich_send_blocks(
            client, 123, [telethon_block_paragraph("hi")]
        )


async def test_plain_send_reraises_flood_wait():
    client = FakeTelethonClient(
        fail={"send_message"}, fail_error=FloodWaitError(None, 5)
    )
    with pytest.raises(FloodWaitError):
        await telethon_rich_send(client, 123, "<b>hello</b>")


async def test_rich_edit_reraises_flood_wait():
    client = FakeTelethonClient(
        fail={"invoke"}, fail_error=FloodWaitError(None, 5)
    )
    message = FakeTelethonMessage(client)
    with pytest.raises(FloodWaitError):
        await telethon_rich_edit(message, RICH)
    assert client.names() == ["invoke"]
