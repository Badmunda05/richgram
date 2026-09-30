from richgram import rich_button, rich_button_row


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
