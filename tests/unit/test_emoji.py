import pytest

from richgram import (
    clear_custom_emojis,
    custom_emoji_names,
    expand_emoji_shortcodes,
    fetch_custom_emoji,
    register_custom_emoji,
    register_custom_emojis,
    rich_emoji,
    rich_emoji_markdown,
    rich_emoji_named,
    rich_text_custom_emoji,
    rich_to_plain,
)
from richgram import rich_ui
from tests.helpers import FakeClient, rich_available

FIRE_ID = "5368324170671202286"


@pytest.fixture(autouse=True)
def _clean_registry():
    clear_custom_emojis()
    yield
    clear_custom_emojis()


def test_rich_emoji_emits_canonical_tg_emoji_tag():
    assert rich_emoji(FIRE_ID, "🔥") == (
        '<tg-emoji emoji-id="5368324170671202286">🔥</tg-emoji>'
    )


def test_rich_emoji_accepts_int_id_and_normalises_leading_zeroes():
    assert rich_emoji(5368324170671202286, "🔥").startswith(
        '<tg-emoji emoji-id="5368324170671202286">'
    )
    assert 'emoji-id="123"' in rich_emoji("000123", "✦")


def test_rich_emoji_escapes_alt_text():
    assert rich_emoji(FIRE_ID, "a<b") == (
        '<tg-emoji emoji-id="5368324170671202286">a&lt;b</tg-emoji>'
    )


@pytest.mark.parametrize("bad_id", ["", "  ", "abc", "12a", "5368-321", "1.5", "+123", None, 3.5, True])
def test_rich_emoji_rejects_bad_ids(bad_id):
    with pytest.raises(ValueError, match="custom emoji id"):
        rich_emoji(bad_id, "🔥")


@pytest.mark.parametrize("bad_id", [0, -1, 2**63])
def test_rich_emoji_rejects_out_of_range_ids(bad_id):
    with pytest.raises(ValueError, match="custom emoji id"):
        rich_emoji(bad_id, "🔥")


@pytest.mark.parametrize("bad_alt", ["", "   ", None, 123])
def test_rich_emoji_requires_alt_text(bad_alt):
    with pytest.raises(ValueError, match="alternative emoji"):
        rich_emoji(FIRE_ID, bad_alt)


def test_rich_emoji_markdown_form():
    assert rich_emoji_markdown(FIRE_ID, "🔥") == "![🔥](tg://emoji?id=5368324170671202286)"
    with pytest.raises(ValueError, match="custom emoji id"):
        rich_emoji_markdown("nope", "🔥")


def test_rich_text_custom_emoji_returns_typed_object():
    emoji = rich_text_custom_emoji(FIRE_ID, "🔥")
    assert emoji.custom_emoji_id == FIRE_ID
    assert emoji.alternative_text == "🔥"


def test_rich_text_custom_emoji_without_support_raises():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(rich_ui, "RichTextCustomEmoji", None)
        with pytest.raises(RuntimeError, match="RichTextCustomEmoji"):
            rich_text_custom_emoji(FIRE_ID, "🔥")


def test_emoji_tag_triggers_rich_path():
    assert rich_ui._has_rich_only_tags("hi " + rich_emoji(FIRE_ID, "🔥"))
    assert rich_ui._has_rich_only_tags('<tg-emoji emoji-id="123">✦</tg-emoji>')
    assert rich_ui._has_rich_only_tags('<emoji id="123">✦</emoji>')


def test_legacy_emoji_tag_is_normalised_to_tg_emoji():
    out = rich_ui._normalize_html('hi <emoji id="123">✦</emoji>')
    assert out == 'hi <tg-emoji emoji-id="123">✦</tg-emoji>'


def test_plain_fallback_keeps_tg_emoji_but_plain_text_strips_to_alt():
    html = "hi " + rich_emoji(FIRE_ID, "🔥")
    assert rich_ui._plain_fallback(html) == html
    assert rich_to_plain(html) == "hi 🔥"


async def test_rich_send_uses_rich_message_for_emoji_only_text():
    client = FakeClient()
    with rich_available(True):
        await rich_ui.rich_send(client, 1, "hi " + rich_emoji(FIRE_ID, "🔥"))
    assert client.names() == ["send_rich_message"]
    assert "tg-emoji" in client.last()["rich_message"].html


async def test_rich_send_plain_fallback_keeps_emoji_tag_when_rich_fails():
    client = FakeClient(fail={"send_rich_message"})
    with rich_available(True):
        await rich_ui.rich_send(client, 1, "hi " + rich_emoji(FIRE_ID, "🔥"))
    assert client.names() == ["send_rich_message", "send_message"]
    assert "tg-emoji" in client.last("send_message")["text"]


def test_register_and_use_by_name():
    assert register_custom_emoji("fire", FIRE_ID, "🔥") == rich_emoji(FIRE_ID, "🔥")
    assert rich_emoji_named("fire") == rich_emoji(FIRE_ID, "🔥")
    assert rich_emoji_named("FIRE") == rich_emoji(FIRE_ID, "🔥")
    assert custom_emoji_names() == ["fire"]


def test_register_rejects_bad_names_ids_and_alts():
    with pytest.raises(ValueError, match="custom emoji name"):
        register_custom_emoji("1fire", FIRE_ID, "🔥")
    with pytest.raises(ValueError, match="custom emoji name"):
        register_custom_emoji("fire night", FIRE_ID, "🔥")
    with pytest.raises(ValueError, match="custom emoji id"):
        register_custom_emoji("fire", "nope", "🔥")
    with pytest.raises(ValueError, match="alternative emoji"):
        register_custom_emoji("fire", FIRE_ID, "")


def test_register_many_tuple_and_dict_forms():
    register_custom_emojis({
        "fire": (FIRE_ID, "🔥"),
        "star": {"id": "5848259999763011021", "alt": "⭐"},
    })
    assert custom_emoji_names() == ["fire", "star"]
    assert "5848259999763011021" in rich_emoji_named("star")


def test_unknown_name_error_lists_registered_names():
    register_custom_emoji("fire", FIRE_ID, "🔥")
    with pytest.raises(KeyError, match="unknown custom emoji 'nope'"):
        rich_emoji_named("nope")


def test_expand_shortcode_replaces_only_registered_names():
    register_custom_emoji("fire", FIRE_ID, "🔥")
    out = expand_emoji_shortcodes("Nice :fire: work! :unknown: stays, 12:30 stays")
    assert out == (
        "Nice " + rich_emoji(FIRE_ID, "🔥") + " work! :unknown: stays, 12:30 stays"
    )


def test_expand_shortcode_skips_pre_and_code():
    register_custom_emoji("fire", FIRE_ID, "🔥")
    out = expand_emoji_shortcodes("<pre>:fire:</pre> <code>:fire:</code> :fire:")
    assert out.count("<tg-emoji ") == 1
    assert "<pre>:fire:</pre>" in out
    assert "<code>:fire:</code>" in out


def test_expand_shortcode_without_registry_is_a_noop():
    assert expand_emoji_shortcodes("hi :fire:") == "hi :fire:"
    assert expand_emoji_shortcodes("") == ""


def test_expand_shortcode_works_as_html_hook():
    register_custom_emoji("fire", FIRE_ID, "🔥")
    rich_ui.add_html_hook(expand_emoji_shortcodes)
    try:
        assert "tg-emoji" in rich_ui._normalize_html("Nice :fire: work!")
    finally:
        rich_ui.clear_html_hooks()


async def test_fetch_custom_emoji_returns_first_sticker():
    from types import SimpleNamespace

    class EmojiClient(FakeClient):
        async def get_custom_emoji_stickers(self, ids):
            assert ids == [FIRE_ID]
            return [SimpleNamespace(custom_emoji_id=FIRE_ID, emoji="🔥")]

    sticker = await fetch_custom_emoji(EmojiClient(), FIRE_ID)
    assert sticker.emoji == "🔥"


async def test_fetch_custom_emoji_returns_none_when_unknown():
    class EmptyClient(FakeClient):
        async def get_custom_emoji_stickers(self, ids):
            return []

    assert await fetch_custom_emoji(EmptyClient(), FIRE_ID) is None


async def test_fetch_custom_emoji_validates_id_and_client():
    with pytest.raises(ValueError, match="custom emoji id"):
        await fetch_custom_emoji(FakeClient(), "nope")
    with pytest.raises(RuntimeError, match="get_custom_emoji_stickers"):
        await fetch_custom_emoji(FakeClient(), FIRE_ID)
