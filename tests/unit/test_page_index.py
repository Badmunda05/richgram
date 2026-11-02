import pytest

from richgram import rich_page_index, rich_to_plain
from richgram import rich_ui


def test_full_index_line():
    assert rich_page_index(2, 5, total=42) == (
        "<footer><i>Page 2 of 5 • total 42</i></footer>"
    )


def test_total_is_optional():
    assert rich_page_index(1, 3) == "<footer><i>Page 1 of 3</i></footer>"


def test_label_names_the_list():
    assert rich_page_index(2, 5, label="Settings") == (
        "<footer><i>Settings • Page 2 of 5</i></footer>"
    )


def test_label_is_escaped():
    assert "a&lt;b" in rich_page_index(1, 1, label="a<b")


def test_rejects_bad_counts():
    with pytest.raises(ValueError, match="1-based"):
        rich_page_index(0, 5)
    with pytest.raises(ValueError, match="1-based"):
        rich_page_index(6, 5)
    with pytest.raises(ValueError, match="1-based"):
        rich_page_index(1, 0)
    with pytest.raises(ValueError, match="1-based"):
        rich_page_index(True, 5)
    with pytest.raises(ValueError, match="1-based"):
        rich_page_index(1, "5")
    with pytest.raises(ValueError, match="non-negative total"):
        rich_page_index(1, 5, total=-1)
    with pytest.raises(ValueError, match="non-negative total"):
        rich_page_index(1, 5, total=True)
    with pytest.raises(ValueError, match="label must be a string"):
        rich_page_index(1, 5, label=42)


def test_page_index_triggers_rich_path_and_survives_fallback():
    html = rich_page_index(2, 5, total=42)
    assert rich_ui._has_rich_only_tags(html)
    assert rich_ui._plain_fallback(html) == "<i>Page 2 of 5 • total 42</i>"
    assert rich_to_plain(html) == "Page 2 of 5 • total 42"
