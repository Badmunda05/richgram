import pytest

from richgram import (
    rich_block_details,
    rich_block_paragraph,
    rich_details,
    rich_details_group,
    rich_details_nested,
    rich_to_plain,
)
from richgram import rich_ui


def test_group_joins_sibling_sections():
    out = rich_details_group([("A", "1"), ("B", "2")])
    assert out == (
        "<details><summary>A</summary>1</details>\n"
        "<details><summary>B</summary>2</details>"
    )


def test_group_accepts_dicts_and_per_section_open():
    out = rich_details_group([
        {"summary": "A", "body": "1"},
        ("B", "2", True),
    ])
    assert "<details><summary>A</summary>1</details>" in out
    assert "<details open><summary>B</summary>2</details>" in out


def test_group_open_first_and_open_all():
    assert rich_details_group([("A", "1"), ("B", "2")], open_first=True).startswith(
        "<details open>"
    )
    assert rich_details_group([("A", "1"), ("B", "2")], open_first=True).count(
        "<details open>"
    ) == 1
    assert rich_details_group([("A", "1"), ("B", "2")], open_all=True).count(
        "<details open>"
    ) == 2


def test_group_per_section_open_wins_over_open_first():
    out = rich_details_group([("A", "1"), ("B", "2", True)], open_first=True)
    assert out.count("<details open>") == 2


def test_group_rejects_both_open_modes():
    with pytest.raises(ValueError, match="open_first and open_all"):
        rich_details_group([("A", "1")], open_first=True, open_all=True)


def test_group_empty_is_empty_string():
    assert rich_details_group([]) == ""
    assert rich_details_group(None) == ""


def test_group_rejects_bad_sections():
    with pytest.raises(ValueError, match="non-empty summary"):
        rich_details_group([("", "1")])
    with pytest.raises(ValueError, match="details section"):
        rich_details_group(["not-a-section"])
    with pytest.raises(ValueError, match="details section"):
        rich_details_group([("A", "1", True, "extra")])


def test_nested_builds_a_tree():
    out = rich_details_nested("Guide", "Start.", children=[
        ("Install", "pip install richgram"),
        {"summary": "Advanced", "body": "", "children": [
            ("Source", "Clone the repo"),
        ]},
    ])
    assert out == (
        "<details><summary>Guide</summary>Start."
        "<details><summary>Install</summary>pip install richgram</details>"
        "<details><summary>Advanced</summary>"
        "<details><summary>Source</summary>Clone the repo</details>"
        "</details></details>"
    )


def test_nested_accepts_prebuilt_details_strings():
    inner = rich_details("Inner", "deep")
    out = rich_details_nested("Outer", "intro ", children=[inner])
    assert out == (
        "<details><summary>Outer</summary>intro "
        "<details><summary>Inner</summary>deep</details></details>"
    )


def test_nested_open_flag_and_empty_body():
    out = rich_details_nested("G", children=[("A", "1")], open=True)
    assert out.startswith("<details open><summary>G</summary>")
    assert "<details><summary>A</summary>1</details>" in out


def test_hand_nested_details_still_work():
    inner = rich_details("Inner", "deep")
    outer = rich_details("Outer", "intro " + inner, open=True)
    assert outer == (
        "<details open><summary>Outer</summary>intro "
        "<details><summary>Inner</summary>deep</details></details>"
    )


def _deep_details(levels):
    text = "x"
    for level in range(levels):
        text = rich_details(f"L{level}", text)
    return text


def test_sixteen_levels_are_allowed_but_seventeen_raise():
    assert _deep_details(16).count("<details") == 16
    with pytest.raises(ValueError, match="16-level limit"):
        _deep_details(17)


def test_nested_tree_depth_limit():
    node = ("L", "x")
    for _ in range(17):
        node = {"summary": "L", "body": "", "children": [node]}
    with pytest.raises(ValueError, match="16-level limit"):
        rich_details_nested("Root", children=[node])


def test_plain_fallback_indents_nested_summaries():
    html = rich_details_nested("G", children=[("A", "1"), ("B", "2", True)])
    out = rich_ui._plain_fallback(html)
    assert out == "▸ <b>G</b>\n  ▸ <b>A</b>\n1\n  ▸ <b>B</b>\n2"


def test_plain_fallback_separates_sibling_sections():
    html = rich_details_group([("A", "1"), ("B", "2")])
    out = rich_ui._plain_fallback(html)
    assert "▸ <b>A</b>\n1" in out
    assert "▸ <b>B</b>\n2" in out
    assert "1<b>B</b>" not in out


def test_rich_to_plain_keeps_nested_outline():
    html = rich_details("Outer", "intro " + rich_details("Inner", "deep"))
    out = rich_to_plain(html)
    assert "▸ Outer" in out
    assert "▸ Inner" in out
    assert "deep" in out
    assert "<details" not in out


def test_nested_details_survive_normalisation():
    html = rich_details("Outer", "a\n" + rich_details("Inner", "b\nc"))
    out = rich_ui._normalize_html(html)
    assert out.count("<details") == 2
    assert out.count("</details>") == 2
    assert "<details><summary>Inner</summary>b<br/>\nc</details>" in out


def test_rich_block_details_returns_typed_object():
    block = rich_block_details("S", [rich_block_paragraph("hello")], open=True)
    assert block.summary == "S"
    assert block.is_open is True
    assert len(block.blocks) == 1
    assert block.blocks[0].text == "hello"


def test_rich_block_details_nests_and_defaults_closed():
    inner = rich_block_details("Inner", [rich_block_paragraph("deep")])
    outer = rich_block_details("Outer", [inner])
    assert outer.is_open is None
    assert outer.blocks[0] is inner


def test_rich_block_details_validates_summary():
    with pytest.raises(ValueError, match="non-empty summary"):
        rich_block_details("", [])


def test_rich_block_helpers_without_support_raise():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(rich_ui, "InputRichBlockDetails", None)
        with pytest.raises(RuntimeError, match="InputRichBlockDetails"):
            rich_block_details("S", [])
        mp.setattr(rich_ui, "InputRichBlockParagraph", None)
        with pytest.raises(RuntimeError, match="InputRichBlockParagraph"):
            rich_block_paragraph("hi")


async def test_rich_send_sends_a_group_as_one_rich_message():
    from tests.helpers import FakeClient, rich_available

    client = FakeClient()
    with rich_available(True):
        await rich_ui.rich_send(
            client, 1, rich_details_group([("A", "1"), ("B", "2")])
        )
    assert client.names() == ["send_rich_message"]
    assert client.last()["rich_message"].html.count("<details") == 2
