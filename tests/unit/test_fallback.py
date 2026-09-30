from richgram import rich_button, rich_caption, rich_to_plain
from richgram import rich_ui


def test_detects_rich_only_tags():
    assert rich_ui._has_rich_only_tags("<h3>x</h3>")
    assert rich_ui._has_rich_only_tags("<table><tr><td>x</td></tr></table>")
    assert rich_ui._has_rich_only_tags('<tg-button type="url" url="https://a">x</tg-button>')
    assert rich_ui._has_rich_only_tags("<tg-button-row></tg-button-row>")
    assert rich_ui._has_rich_only_tags("<ul><li>x</li></ul>")
    assert rich_ui._has_rich_only_tags("<hr/>")
    assert rich_ui._has_rich_only_tags("<tg-math-block>x</tg-math-block>")


def test_plain_html_is_not_rich():
    assert not rich_ui._has_rich_only_tags("<b>bold</b> and <i>italic</i> and <code>x</code>")
    assert not rich_ui._has_rich_only_tags("")
    assert not rich_ui._has_rich_only_tags(None)


def test_url_button_becomes_a_link():
    html = rich_button("Support", url="https://t.me/x", style="primary")
    assert rich_ui._plain_fallback(html) == '<a href="https://t.me/x">Support</a>'


def test_callback_button_becomes_bold_text():
    html = rich_button("Pause", callback_data="pause", style="success")
    assert rich_ui._plain_fallback(html) == "<b>Pause</b>"


def test_legacy_url_button_format_still_falls_back_to_a_link():
    legacy = '<tg-button url="https://t.me/x">Go</tg-button>'
    assert rich_ui._plain_fallback(legacy) == '<a href="https://t.me/x">Go</a>'


def test_button_row_and_lists_fall_back_to_lines():
    html = (
        "<ul><li>one</li><li>two</li></ul>"
        + "<tg-button-row>"
        + rich_button("A", callback_data="a")
        + "</tg-button-row>"
    )
    out = rich_ui._plain_fallback(html)
    assert "\u2022 one" in out
    assert "\u2022 two" in out
    assert "<b>A</b>" in out
    assert "<ul>" not in out and "<tg-button" not in out


def test_headings_become_bold_and_tables_flatten():
    out = rich_ui._plain_fallback("<h3>Title</h3><table><tr><td>a</td><td>b</td></tr></table>")
    assert "<b>Title</b>" in out
    assert "<table" not in out and "<td" not in out


def test_math_falls_back_to_code():
    assert rich_ui._plain_fallback("<tg-math-block>x^2</tg-math-block>") == "<code>x^2</code>"


def test_rich_caption_is_the_plain_fallback():
    assert rich_caption("<h3>Hi</h3>") == rich_ui._plain_fallback("<h3>Hi</h3>")


def test_rich_to_plain_strips_everything():
    html = "<h3>Title</h3><ul><li>one</li></ul><b>x</b> &amp; y"
    out = rich_to_plain(html)
    assert "<" not in out
    assert "Title" in out and "\u2022 one" in out and "x & y" in out


def test_empty_inputs():
    assert rich_to_plain("") == ""
    assert rich_to_plain(None) == ""
    assert rich_ui._plain_fallback("") == ""


def test_newlines_become_br_outside_tables_and_pre():
    out = rich_ui._normalize_html("a\nb")
    assert out == "a<br/>\nb"
    pre = rich_ui._normalize_html("<pre>a\nb</pre>")
    assert pre == "<pre>a\nb</pre>"


def test_href_quotes_are_normalised():
    assert rich_ui._normalize_html("<a href='https://x'>x</a>") == '<a href="https://x">x</a>'


def test_html_hooks_transform_and_can_be_cleared():
    def upper_marker(text):
        return text.replace("[[x]]", "<b>X</b>")

    rich_ui.add_html_hook(upper_marker)
    try:
        assert "<b>X</b>" in rich_ui._normalize_html("hi [[x]]")
    finally:
        rich_ui.clear_html_hooks()
    assert "[[x]]" in rich_ui._normalize_html("hi [[x]]")


def test_failing_hook_is_skipped():
    def broken(text):
        raise ValueError("boom")

    rich_ui.add_html_hook(broken)
    try:
        assert rich_ui._normalize_html("hello") == "hello"
    finally:
        rich_ui.clear_html_hooks()
