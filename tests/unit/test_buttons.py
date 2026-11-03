import pytest

from richgram import rich_button, rich_button_row
from richgram import rich_ui
from richgram.telethon import telethon_rich_send

from tests.unit.test_telethon import FakeTelethonClient


def test_url_button_layout_matches_pills():
    html = rich_button("Support", url="https://t.me/x", style="primary")
    assert html == '<tg-button type="url" style="primary" url="https://t.me/x">Support</tg-button>'


def test_callback_button_layout():
    html = rich_button("Pause", callback_data="pause", style="success")
    assert html == '<tg-button type="callback_data" style="success" data="pause">Pause</tg-button>'


def test_callback_wins_over_url():
    html = rich_button("X", url="https://a", callback_data="cb")
    assert 'type="callback_data"' in html
    assert "url=" not in html


def test_no_style_means_grey_button():
    assert "style=" not in rich_button("Queue", callback_data="q")


def test_unknown_style_is_ignored():
    assert "style=" not in rich_button("X", callback_data="q", style="rainbow")


def test_every_known_style_is_accepted():
    for style in ("primary", "success", "danger", "link", "default"):
        assert f'style="{style}"' in rich_button("X", callback_data="q", style=style)


def test_attribute_values_are_escaped():
    html = rich_button("X", callback_data='a"b<c')
    assert 'data="a&quot;b&lt;c"' in html


def test_button_without_action():
    assert rich_button("Plain", style="danger") == '<tg-button style="danger">Plain</tg-button>'


def test_row_wraps_buttons():
    a = rich_button("A", callback_data="a")
    b = rich_button("B", callback_data="b")
    assert rich_button_row(a, b) == f"<tg-button-row>{a}{b}</tg-button-row>"


def test_row_accepts_a_list():
    a = rich_button("A", callback_data="a")
    assert rich_button_row([a]) == f"<tg-button-row>{a}</tg-button-row>"


def test_row_alignment():
    assert rich_button_row(align="center").startswith('<tg-button-row align="center">')
    assert rich_button_row(align="sideways") == "<tg-button-row></tg-button-row>"


def test_copy_button_layout():
    html = rich_button("Copy ID", copy_text="5368324170671202286", style="primary")
    assert html == (
        '<tg-button type="copy_text" style="primary" '
        'text="5368324170671202286">Copy ID</tg-button>'
    )


def test_copy_button_without_style():
    assert rich_button("Copy", copy_text="abc") == (
        '<tg-button type="copy_text" text="abc">Copy</tg-button>'
    )


def test_copy_text_is_escaped():
    html = rich_button("Copy", copy_text='a"b<c')
    assert 'text="a&quot;b&lt;c"' in html


def test_copy_text_limits():
    with pytest.raises(ValueError, match="1-256 characters"):
        rich_button("Copy", copy_text="")
    with pytest.raises(ValueError, match="1-256 characters"):
        rich_button("Copy", copy_text="x" * 257)
    with pytest.raises(ValueError, match="1-256 characters"):
        rich_button("Copy", copy_text="a\x00b")
    with pytest.raises(ValueError, match="1-256 characters"):
        rich_button("Copy", copy_text=42)
    assert 'text="' + "x" * 256 + '"' in rich_button("Copy", copy_text="x" * 256)


def test_copy_button_takes_no_other_action():
    with pytest.raises(ValueError, match="only copy_text"):
        rich_button("Copy", copy_text="abc", url="https://a")
    with pytest.raises(ValueError, match="only copy_text"):
        rich_button("Copy", copy_text="abc", callback_data="cb")


def test_copy_button_falls_back_to_bold_label():
    html = rich_button("Copy ID", copy_text="abc")
    assert rich_ui._has_rich_only_tags(html)
    assert rich_ui._plain_fallback(html) == "<b>Copy ID</b>"
    assert "abc" not in rich_ui._plain_fallback(html)


async def test_copy_button_sends_rich_over_telethon():
    client = FakeTelethonClient()
    await telethon_rich_send(client, 123, rich_button("Copy", copy_text="abc"))
    assert client.names() == ["invoke"]
    assert 'type="copy_text"' in client.last("invoke").rich_message.html
