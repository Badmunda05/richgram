import pytest
from pyrogram import types as kurigram_types
from telethon import types as telethon_types

from richgram import (
    rich_block_todo_list,
    rich_send,
    rich_to_plain,
    rich_todo_list,
    rich_todo_list_markdown,
)
from richgram import rich_ui
from richgram.telethon import telethon_block_todo_list, telethon_rich_send_blocks
from tests.helpers import FakeClient, rich_available

from tests.unit.test_telethon import FakeTelethonClient

ITEMS = [("Buy milk", False), ("Book tickets", True), "Call mom"]


def test_html_renders_native_checkboxes():
    assert rich_todo_list(ITEMS) == (
        "<ul>"
        '<li><input type="checkbox">Buy milk</li>'
        '<li><input type="checkbox" checked>Book tickets</li>'
        '<li><input type="checkbox">Call mom</li>'
        "</ul>"
    )


def test_html_accepts_dict_items_and_empty_input():
    assert rich_todo_list([{"text": "Ship it", "done": True}]) == (
        "<ul>" '<li><input type="checkbox" checked>Ship it</li>' "</ul>"
    )
    assert rich_todo_list([]) == "<ul></ul>"
    assert rich_todo_list(None) == "<ul></ul>"


def test_markdown_task_list():
    assert rich_todo_list_markdown(ITEMS) == (
        "- [ ] Buy milk\n- [x] Book tickets\n- [ ] Call mom"
    )


def test_markdown_rejects_multiline_text():
    with pytest.raises(ValueError, match="single line"):
        rich_todo_list_markdown([("one\ntwo", False)])


def test_rejects_bad_item_forms():
    with pytest.raises(ValueError, match="todo item"):
        rich_todo_list([42])
    with pytest.raises(ValueError, match="todo item"):
        rich_todo_list([("a", "b", "c")])
    with pytest.raises(ValueError, match="text must be a string"):
        rich_todo_list([(42, False)])
    with pytest.raises(ValueError, match="done flag must be True or False"):
        rich_todo_list([("a", 1)])
    with pytest.raises(ValueError, match="done flag must be True or False"):
        rich_todo_list([{"text": "a", "done": "yes"}])


def test_typed_block_checkboxes():
    block = rich_block_todo_list(ITEMS)
    assert isinstance(block, kurigram_types.InputRichBlockList)
    assert [item.has_checkbox for item in block.items] == [True, True, True]
    assert [item.is_checked for item in block.items] == [False, True, False]
    texts = [item.blocks[0].text for item in block.items]
    assert texts == ["Buy milk", "Book tickets", "Call mom"]


def test_typed_block_without_kurigram_types_raises(monkeypatch):
    monkeypatch.setattr(rich_ui, "InputRichBlockList", None)
    with pytest.raises(RuntimeError, match="InputRichBlockList"):
        rich_block_todo_list(ITEMS)


def test_telethon_block_checkboxes():
    block = telethon_block_todo_list(ITEMS)
    assert isinstance(block, telethon_types.PageBlockList)
    assert [item.checkbox for item in block.items] == [True, True, True]
    assert [item.checked for item in block.items] == [False, True, False]
    assert [item.text for item in block.items] == [
        "Buy milk",
        "Book tickets",
        "Call mom",
    ]


def test_plain_fallback_renders_boxes_not_bullets():
    html = rich_todo_list(ITEMS)
    assert rich_ui._plain_fallback(html) == (
        "[ ] Buy milk\n[x] Book tickets\n[ ] Call mom"
    )
    assert rich_to_plain(html) == "[ ] Buy milk\n[x] Book tickets\n[ ] Call mom"
    assert "<input" not in rich_ui._plain_fallback(html)
    assert "<input" not in rich_to_plain(html)


def test_plain_list_still_uses_bullets():
    assert rich_to_plain("<ul><li>one</li><li>two</li></ul>") == "• one\n• two"


async def test_rich_send_sends_todo_as_rich():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 123, rich_todo_list(ITEMS))
    assert client.names() == ["send_rich_message"]
    payload = client.last("send_rich_message")["rich_message"]
    assert '<input type="checkbox" checked>Book tickets' in payload.html


async def test_markdown_todo_sends_as_markdown():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 123, rich_todo_list_markdown(ITEMS), markdown=True)
    payload = client.last("send_rich_message")["rich_message"]
    assert payload.markdown == "- [ ] Buy milk\n- [x] Book tickets\n- [ ] Call mom"


async def test_telethon_send_blocks_with_todo():
    client = FakeTelethonClient()
    await telethon_rich_send_blocks(client, 123, [telethon_block_todo_list(ITEMS)])
    assert client.names() == ["invoke"]
    request = client.last("invoke")
    block = request.rich_message.blocks[0]
    assert isinstance(block, telethon_types.PageBlockList)
    assert [item.checked for item in block.items] == [False, True, False]
