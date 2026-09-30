from types import SimpleNamespace

from richgram import (
    RichDraft,
    ephemeral_delete,
    ephemeral_edit,
    rich_answer,
    rich_button,
    rich_edit,
    rich_edit_inline,
    rich_heading,
    rich_reply,
    rich_send,
    rich_send_blocks,
)
from tests.helpers import FakeCallbackQuery, FakeClient, FakeMessage, rich_available

RICH = rich_heading("Hi", level=3)
KB = rich_button("Go", callback_data="go")


async def test_rich_send_uses_rich_message_for_rich_html():
    client = FakeClient()
    with rich_available(True):
        result = await rich_send(client, 1, RICH)
    assert client.names() == ["send_rich_message"]
    assert "<h3>Hi</h3>" in client.last()["rich_message"].html
    assert client.last()["chat_id"] == 1
    assert result.call == "send_rich_message"


async def test_rich_send_plain_html_uses_send_message():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 1, "<b>hello</b>")
    assert client.names() == ["send_message"]
    assert client.last()["text"] == "<b>hello</b>"


async def test_rich_send_falls_back_when_rich_fails():
    client = FakeClient(fail={"send_rich_message"})
    with rich_available(True):
        result = await rich_send(client, 1, RICH + KB)
    assert client.names() == ["send_rich_message", "send_message"]
    text = client.last("send_message")["text"]
    assert "<b>Hi</b>" in text and "<b>Go</b>" in text
    assert "<tg-button" not in text
    assert result.call == "send_message"


async def test_rich_send_falls_back_when_rich_unavailable():
    client = FakeClient()
    with rich_available(False):
        await rich_send(client, 1, RICH)
    assert client.names() == ["send_message"]


async def test_rich_send_returns_none_when_everything_fails():
    client = FakeClient(fail={"send_rich_message", "send_message"})
    with rich_available(True):
        assert await rich_send(client, 1, RICH) is None


async def test_rich_send_empty_text_sends_nothing():
    client = FakeClient()
    assert await rich_send(client, 1, "") is None
    assert client.calls == []


async def test_buttons_travel_inside_the_content():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 1, RICH + KB)
    html = client.last()["rich_message"].html
    assert 'type="callback_data"' in html and 'data="go"' in html
    assert "reply_markup" not in client.last()


async def test_reply_markup_and_markup_alias_are_forwarded():
    client = FakeClient()
    marker = object()
    with rich_available(True):
        await rich_send(client, 1, RICH, markup=marker)
    assert client.last()["reply_markup"] is marker


async def test_optional_arguments_are_only_sent_when_set():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 1, RICH)
    assert set(client.last()) == {"chat_id", "rich_message"}


async def test_extra_send_arguments_are_forwarded():
    client = FakeClient()
    with rich_available(True):
        await rich_send(
            client, 1, RICH,
            business_connection_id="bc1",
            direct_messages_topic_id=5,
            allow_paid_broadcast=True,
            message_thread_id=9,
            disable_notification=True,
            protect_content=True,
            effect_id=77,
        )
    sent = client.last()
    assert sent["business_connection_id"] == "bc1"
    assert sent["direct_messages_topic_id"] == 5
    assert sent["allow_paid_broadcast"] is True
    assert sent["message_thread_id"] == 9
    assert sent["disable_notification"] is True
    assert sent["protect_content"] is True
    assert sent["effect_id"] == 77


async def test_extra_send_arguments_survive_the_plain_fallback():
    client = FakeClient(fail={"send_rich_message"})
    with rich_available(True):
        await rich_send(client, 1, RICH, business_connection_id="bc1", message_thread_id=3)
    sent = client.last("send_message")
    assert sent["business_connection_id"] == "bc1"
    assert sent["message_thread_id"] == 3


async def test_reply_to_message_id_becomes_reply_parameters():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 1, RICH, reply_to_message_id=55)
    assert client.last()["reply_parameters"].message_id == 55


async def test_ephemeral_send_forces_rich_and_sets_receiver():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 1, "<b>plain</b>", receiver_user_id=42, callback_query_id="cb")
    assert client.names() == ["send_rich_message"]
    params = client.last()["ephemeral_message_parameters"]
    assert params.receiver_user_id == 42
    assert params.callback_query_id == "cb"


async def test_ephemeral_send_stays_ephemeral_when_falling_back():
    client = FakeClient(fail={"send_rich_message"})
    with rich_available(True):
        await rich_send(client, 1, RICH, receiver_user_id=42)
    assert client.last("send_message")["ephemeral_message_parameters"].receiver_user_id == 42


async def test_markdown_mode_uses_rich_markdown():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 1, "# Title\n\ntext", markdown=True)
    message = client.last()["rich_message"]
    assert message.markdown == "# Title\n\ntext"
    assert message.html is None


async def test_markdown_mode_falls_back_to_markdown_parse_mode():
    client = FakeClient()
    with rich_available(False):
        await rich_send(client, 1, "*bold*", markdown=True)
    sent = client.last("send_message")
    assert sent["text"] == "*bold*"
    assert sent["parse_mode"].value == "markdown"


async def test_rich_message_options_are_forwarded():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 1, RICH, is_rtl=True, skip_entity_detection=True)
    message = client.last()["rich_message"]
    assert message.is_rtl is True
    assert message.skip_entity_detection is True


async def test_unknown_keyword_arguments_are_ignored():
    client = FakeClient()
    with rich_available(True):
        await rich_send(client, 1, RICH, totally_unknown=1)
    assert client.names() == ["send_rich_message"]


async def test_send_blocks_uses_native_typed_blocks():
    client = FakeClient()
    blocks = [SimpleNamespace(kind="map"), SimpleNamespace(kind="collage")]
    with rich_available(True):
        await rich_send_blocks(client, 1, blocks, message_thread_id=4, is_rtl=True)
    sent = client.last()
    assert sent["rich_message"].blocks == blocks
    assert sent["rich_message"].is_rtl is True
    assert sent["message_thread_id"] == 4


async def test_send_blocks_needs_blocks_and_rich_support():
    client = FakeClient()
    assert await rich_send_blocks(client, 1, []) is None
    with rich_available(False):
        assert await rich_send_blocks(client, 1, [SimpleNamespace()]) is None
    assert client.calls == []


async def test_send_blocks_failure_returns_none():
    client = FakeClient(fail={"send_rich_message"})
    with rich_available(True):
        assert await rich_send_blocks(client, 1, [SimpleNamespace()]) is None


async def test_send_blocks_dict_blocks_need_a_token():
    client = FakeClient()
    assert await rich_send_blocks(client, 1, [{"type": "paragraph"}]) is None
    assert client.calls == []


async def test_reply_to_message_quotes_and_uses_chat():
    message = FakeMessage(chat_id=200, message_id=9)
    with rich_available(True):
        await rich_reply(message, RICH)
    sent = message._client.last()
    assert sent["chat_id"] == 200
    assert sent["reply_parameters"].message_id == 9


async def test_reply_without_quote_has_no_reply_parameters():
    message = FakeMessage()
    with rich_available(True):
        await rich_reply(message, RICH, quote=False)
    assert "reply_parameters" not in message._client.last()


async def test_reply_ephemeral_in_group_targets_the_sender():
    message = FakeMessage(chat_type="supergroup", user_id=77)
    with rich_available(True):
        await rich_reply(message, RICH, ephemeral=True)
    sent = message._client.last()
    assert sent["ephemeral_message_parameters"].receiver_user_id == 77
    assert "reply_parameters" not in sent


async def test_reply_ephemeral_is_ignored_in_private_chat():
    message = FakeMessage(chat_type="private")
    with rich_available(True):
        await rich_reply(message, RICH, ephemeral=True)
    assert "ephemeral_message_parameters" not in message._client.last()


async def test_reply_to_callback_query_uses_inner_message():
    cbq = FakeCallbackQuery()
    with rich_available(True):
        await rich_reply(cbq, RICH)
    assert cbq._client.last()["chat_id"] == cbq.message.chat.id


async def test_reply_forwards_extra_arguments():
    message = FakeMessage()
    with rich_available(True):
        await rich_reply(message, RICH, business_connection_id="bc9")
    assert message._client.last()["business_connection_id"] == "bc9"


async def test_reply_empty_or_chatless_returns_none():
    message = FakeMessage()
    assert await rich_reply(message, "") is None
    assert await rich_reply(SimpleNamespace(), RICH) is None


async def test_answer_in_group_is_ephemeral():
    cbq = FakeCallbackQuery(chat_type="supergroup")
    with rich_available(True):
        await rich_answer(cbq, RICH)
    params = cbq._client.last()["ephemeral_message_parameters"]
    assert params.receiver_user_id == 42
    assert params.callback_query_id == "cbq-1"


async def test_answer_in_private_chat_is_a_normal_message():
    cbq = FakeCallbackQuery(chat_type="private")
    with rich_available(True):
        await rich_answer(cbq, RICH)
    assert "ephemeral_message_parameters" not in cbq._client.last()


async def test_edit_message_uses_rich_message():
    message = FakeMessage()
    with rich_available(True):
        await rich_edit(message, RICH)
    sent = message._client.last()
    assert message._client.names() == ["edit_message_text"]
    assert sent["chat_id"] == message.chat.id
    assert sent["message_id"] == message.id
    assert "<h3>Hi</h3>" in sent["rich_message"].html


async def test_edit_callback_query_edits_its_message():
    cbq = FakeCallbackQuery()
    with rich_available(True):
        await rich_edit(cbq, RICH + KB)
    sent = cbq._client.last()
    assert sent["message_id"] == cbq.message.id
    assert 'data="go"' in sent["rich_message"].html


async def test_edit_with_client_and_ids():
    client = FakeClient()
    with rich_available(True):
        await rich_edit(client, RICH, chat_id=5, message_id=6)
    assert client.last()["chat_id"] == 5
    assert client.last()["message_id"] == 6


async def test_edit_falls_back_to_plain_text():
    message = FakeMessage()
    message._client.fail = {"edit_message_text"}
    with rich_available(False):
        assert await rich_edit(message, RICH) is None
    assert message._client.last()["text"] == "<b>Hi</b>"


async def test_edit_plain_fallback_after_rich_failure():
    client = FakeClient()
    calls = {"n": 0}

    async def flaky(**kwargs):
        calls["n"] += 1
        client.calls.append(("edit_message_text", kwargs))
        if "rich_message" in kwargs:
            raise RuntimeError("rich rejected")
        return SimpleNamespace(id=1, call="edit_message_text")

    client.edit_message_text = flaky
    with rich_available(True):
        result = await rich_edit(client, RICH, chat_id=1, message_id=2)
    assert calls["n"] == 2
    assert result is not None
    assert client.last()["text"] == "<b>Hi</b>"


async def test_edit_not_modified_is_swallowed():
    message = FakeMessage()
    message._client.not_modified = {"edit_message_text"}
    with rich_available(True):
        assert await rich_edit(message, RICH) is None


async def test_edit_needs_ids():
    client = FakeClient()
    assert await rich_edit(client, RICH) is None
    assert client.calls == []


async def test_edit_forwards_business_connection_and_markdown():
    message = FakeMessage()
    with rich_available(True):
        await rich_edit(message, "# hi", business_connection_id="bc2", markdown=True)
    sent = message._client.last()
    assert sent["business_connection_id"] == "bc2"
    assert sent["rich_message"].markdown == "# hi"


async def test_edit_inline_message_uses_rich_message():
    client = FakeClient()
    with rich_available(True):
        await rich_edit_inline(client, "inline-1", RICH)
    sent = client.last()
    assert client.names() == ["edit_inline_text"]
    assert sent["inline_message_id"] == "inline-1"
    assert "<h3>Hi</h3>" in sent["rich_message"].html


async def test_edit_inline_falls_back_to_text():
    client = FakeClient()
    with rich_available(False):
        await rich_edit_inline(client, "inline-1", RICH)
    assert client.last()["text"] == "<b>Hi</b>"


async def test_edit_inline_not_modified_and_missing_id():
    client = FakeClient(not_modified={"edit_inline_text"})
    with rich_available(True):
        assert await rich_edit_inline(client, "inline-1", RICH) is None
    assert await rich_edit_inline(client, "", RICH) is None


async def test_edit_routes_inline_callbacks_to_inline_edit():
    cbq = FakeCallbackQuery(inline_message_id="inline-9")
    with rich_available(True):
        await rich_edit(cbq, RICH)
    assert cbq._client.names() == ["edit_inline_text"]
    assert cbq._client.last()["inline_message_id"] == "inline-9"


def ephemeral_message(client):
    message = FakeMessage(client, ephemeral_message_id=88, chat_id=300)
    message.receiver_user = SimpleNamespace(id=42)
    return message


async def test_ephemeral_edit_sends_rich_message():
    message = ephemeral_message(FakeClient())
    with rich_available(True):
        await ephemeral_edit(message, RICH)
    sent = message._client.last()
    assert message._client.names() == ["edit_ephemeral_message_text"]
    assert sent["chat_id"] == 300
    assert sent["receiver_user_id"] == 42
    assert sent["ephemeral_message_id"] == 88
    assert "<h3>Hi</h3>" in sent["rich_message"].html


async def test_ephemeral_edit_falls_back_to_plain_text():
    message = ephemeral_message(FakeClient())
    with rich_available(False):
        await ephemeral_edit(message, RICH)
    assert message._client.last()["text"] == "<b>Hi</b>"


async def test_ephemeral_edit_on_normal_message_is_a_normal_edit():
    message = FakeMessage()
    with rich_available(True):
        await ephemeral_edit(message, RICH)
    assert message._client.names() == ["edit_message_text"]


async def test_ephemeral_delete_uses_dedicated_method():
    message = ephemeral_message(FakeClient())
    assert await ephemeral_delete(message) is True
    assert message._client.names() == ["delete_ephemeral_message"]
    assert message._client.last()["ephemeral_message_id"] == 88


async def test_ephemeral_delete_on_normal_message_deletes_it():
    message = FakeMessage()
    assert await ephemeral_delete(message) is True
    assert message.deleted is True


async def test_ephemeral_delete_handles_none_and_failure():
    assert await ephemeral_delete(None) is False
    message = ephemeral_message(FakeClient(fail={"delete_ephemeral_message"}))
    assert await ephemeral_delete(message) is False


async def test_draft_streams_then_persists():
    client = FakeClient()
    with rich_available(True):
        async with RichDraft(client, 1, message_thread_id=3, can_stop=True, keep_on_stop=False) as draft:
            assert await draft.update(rich_heading("Working")) is True
            await draft.finish(rich_heading("Done"))
    assert client.names() == ["send_rich_message_draft", "send_rich_message"]
    draft_call = client.calls[0][1]
    assert draft_call["can_stop"] is True
    assert draft_call["keep_on_stop"] is False
    assert draft_call["message_thread_id"] == 3
    assert "<h1>Done</h1>" in client.last("send_rich_message")["rich_message"].html
    assert draft.result is not None


async def test_draft_auto_finishes_with_last_update():
    client = FakeClient()
    with rich_available(True):
        async with RichDraft(client, 1) as draft:
            await draft.update(rich_heading("Only frame"))
    assert client.names() == ["send_rich_message_draft", "send_rich_message"]
    assert "Only frame" in client.last("send_rich_message")["rich_message"].html


async def test_draft_discard_leaves_nothing_behind():
    client = FakeClient()
    with rich_available(True):
        async with RichDraft(client, 1) as draft:
            await draft.update(rich_heading("Progress"))
            draft.discard()
    assert client.names() == ["send_rich_message_draft"]


async def test_draft_failure_downgrades_to_final_send_only():
    client = FakeClient(fail={"send_rich_message_draft"})
    with rich_available(True):
        async with RichDraft(client, 1) as draft:
            assert await draft.update(rich_heading("A")) is False
            assert await draft.update(rich_heading("B")) is False
    assert client.names() == ["send_rich_message_draft", "send_rich_message"]


async def test_draft_ignores_empty_updates_and_empty_finish():
    client = FakeClient()
    with rich_available(True):
        draft = RichDraft(client, 1)
        assert await draft.update("") is False
        assert await draft.finish() is None
    assert client.calls == []
