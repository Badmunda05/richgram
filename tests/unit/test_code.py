import pytest
from pyrogram import types as kurigram_types
from telethon import types as telethon_types

from richgram import (
    rich_block_preformatted,
    rich_pre,
    rich_pre_rich,
    rich_send,
    rich_text_bold,
    rich_text_code,
    rich_text_italic,
    rich_to_plain,
)
from richgram import rich_ui
from richgram.telethon import (
    telethon_block_preformatted,
    telethon_rich_send_blocks,
)
from tests.helpers import FakeClient, rich_available

from tests.unit.test_telethon import FakeTelethonClient

SEGMENTS = [("bold", "pip"), " install ", ("code", "richgram")]


def test_rich_pre_still_escapes_everything():
    assert rich_pre("<b>x</b>", language="python") == (
        '<pre><code class="language-python">&lt;b&gt;x&lt;/b&gt;</code></pre>'
    )


def test_rich_pre_rich_keeps_nested_markup():
    assert rich_pre_rich("<b>pip</b> install <code>richgram</code>", language="bash") == (
        '<pre><code class="language-bash"><b>pip</b> install '
        "<code>richgram</code></code></pre>"
    )
    assert rich_pre_rich("plain") == "<pre>plain</pre>"


def test_nested_pre_parses_as_entities_inside_pre():
    from telethon.extensions.html import parse as parse_html

    text, entities = parse_html(
        rich_pre_rich("<b>pip</b> install <code>richgram</code>", language="bash")
    )
    assert text == "pip install richgram"
    kinds = {type(e).__name__ for e in entities}
    assert "MessageEntityPre" in kinds
    assert "MessageEntityBold" in kinds
    pre = [e for e in entities if type(e).__name__ == "MessageEntityPre"][0]
    assert pre.language == "bash"


def test_typed_pre_plain_string():
    block = rich_block_preformatted("x = 1", language="python")
    assert isinstance(block, kurigram_types.InputRichBlockPreformatted)
    assert block.text == "x = 1"
    assert block.language == "python"


def test_typed_pre_segments():
    block = rich_block_preformatted(SEGMENTS, language="bash")
    assert isinstance(block, kurigram_types.InputRichBlockPreformatted)
    assert [type(item).__name__ for item in block.text] == [
        "RichTextBold",
        "str",
        "RichTextCode",
    ]
    assert block.text[0].text == "pip"
    assert block.text[2].text == "richgram"


def test_typed_pre_accepts_rich_text_objects():
    block = rich_block_preformatted([rich_text_bold("kw"), " = 1"])
    assert isinstance(block.text[0], kurigram_types.RichTextBold)
    assert block.text[1] == " = 1"


def test_rich_text_helpers():
    assert isinstance(rich_text_bold("x"), kurigram_types.RichTextBold)
    assert isinstance(rich_text_italic("x"), kurigram_types.RichTextItalic)
    assert isinstance(rich_text_code("x"), kurigram_types.RichTextCode)
    assert rich_text_bold(rich_text_code("x")).text.text == "x"


def test_typed_pre_rejects_bad_segments():
    with pytest.raises(ValueError, match="preformatted content"):
        rich_block_preformatted([42])
    with pytest.raises(ValueError, match="preformatted content"):
        rich_block_preformatted([("underline", "x")])
    with pytest.raises(ValueError, match="preformatted content"):
        rich_block_preformatted([("bold", 42)])
    with pytest.raises(ValueError, match="language must be a string"):
        rich_block_preformatted("x", language=42)


def test_typed_pre_without_kurigram_types_raises(monkeypatch):
    monkeypatch.setattr(rich_ui, "InputRichBlockPreformatted", None)
    with pytest.raises(RuntimeError, match="InputRichBlockPreformatted"):
        rich_block_preformatted("x")


def test_telethon_pre_segments():
    block = telethon_block_preformatted(SEGMENTS, language="bash")
    assert isinstance(block, telethon_types.PageBlockPreformatted)
    assert block.language == "bash"
    assert isinstance(block.text, telethon_types.TextConcat)
    kinds = [type(item).__name__ for item in block.text.texts]
    assert kinds == ["TextBold", "TextPlain", "TextFixed"]


def test_telethon_pre_plain_string_needs_no_language():
    block = telethon_block_preformatted("x = 1")
    assert isinstance(block.text, telethon_types.TextPlain)
    assert block.language == ""


def test_telethon_pre_rejects_kurigram_objects_and_bad_language():
    with pytest.raises(ValueError, match="Kurigram RichText"):
        telethon_block_preformatted([rich_text_bold("x")])
    with pytest.raises(ValueError, match="language must be a string"):
        telethon_block_preformatted("x", language=42)


def test_nested_pre_plain_text_stays_readable():
    html = rich_pre_rich("<b>pip</b> install <code>richgram</code>", language="bash")
    assert rich_to_plain(html) == "pip install richgram"


async def test_rich_pre_rich_sends_with_nested_markup():
    client = FakeClient()
    with rich_available(True):
        await rich_send(
            client, 123, rich_pre_rich("<b>x</b>", language="python")
        )
    assert client.names() == ["send_message"]
    assert "<b>x</b>" in client.last("send_message")["text"]


async def test_rich_pre_rich_joins_the_rich_path_with_rich_tags():
    from richgram import rich_heading

    client = FakeClient()
    with rich_available(True):
        await rich_send(
            client, 123,
            rich_heading("Code", level=3)
            + rich_pre_rich("<b>x</b>", language="python"),
        )
    assert client.names() == ["send_rich_message"]
    payload = client.last("send_rich_message")["rich_message"]
    assert "<b>x</b>" in payload.html


async def test_telethon_send_blocks_with_nested_pre():
    client = FakeTelethonClient()
    await telethon_rich_send_blocks(
        client, 123, [telethon_block_preformatted(SEGMENTS, language="bash")]
    )
    assert client.names() == ["invoke"]
    block = client.last("invoke").rich_message.blocks[0]
    assert isinstance(block, telethon_types.PageBlockPreformatted)
    assert block.language == "bash"
