import richgram
from richgram import (
    rich_anchor,
    rich_code,
    rich_details,
    rich_esc,
    rich_footer,
    rich_heading,
    rich_hr,
    rich_img,
    rich_kv_table,
    rich_list,
    rich_math,
    rich_note,
    rich_pre,
    rich_pull_quote,
    rich_table,
    rich_thinking,
    sanitize_display_name,
)


def test_version_is_a_string():
    assert isinstance(richgram.__version__, str)
    assert richgram.__version__.count(".") == 2


def test_esc_escapes_html_but_not_quotes():
    assert rich_esc("A & B <song>") == "A &amp; B &lt;song&gt;"
    assert rich_esc('say "hi"') == 'say "hi"'


def test_esc_none_is_empty():
    assert rich_esc(None) == ""


def test_heading_levels_are_clamped():
    assert rich_heading("x", level=3) == "<h3>x</h3>"
    assert rich_heading("x", level=0) == "<h1>x</h1>"
    assert rich_heading("x", level=99) == "<h6>x</h6>"


def test_note_and_expandable_note():
    assert rich_note("hi") == "<blockquote>hi</blockquote>"
    assert rich_note("hi", expandable=True) == "<blockquote expandable>hi</blockquote>"


def test_code_is_escaped():
    assert rich_code("<b>") == "<code>&lt;b&gt;</code>"


def test_pre_with_and_without_language():
    assert rich_pre("a<b") == "<pre>a&lt;b</pre>"
    assert rich_pre("x", language="python") == '<pre><code class="language-python">x</code></pre>'


def test_list_unordered_and_ordered():
    assert rich_list(["a", "b"]) == "<ul><li>a</li><li>b</li></ul>"
    assert rich_list(["a"], ordered=True) == "<ol><li>a</li></ol>"
    assert rich_list([]) == "<ul></ul>"


def test_simple_blocks():
    assert rich_hr() == "<hr/>"
    assert rich_footer("f") == "<footer>f</footer>"
    assert rich_pull_quote("q") == "<aside>q</aside>"
    assert rich_thinking() == "<tg-thinking></tg-thinking>"


def test_math_is_escaped():
    assert rich_math("a<b") == "<tg-math-block>a&lt;b</tg-math-block>"


def test_anchor_attribute_is_escaped():
    assert rich_anchor('a"b') == '<a name="a&quot;b"></a>'


def test_img():
    assert rich_img("https://x/y.png") == '<img src="https://x/y.png" />'
    assert rich_img("") == ""


def test_table_with_headers_and_rows():
    html = rich_table(["A", "B"], [[1, None], [2, 3]])
    assert html.startswith('<table border="1">')
    assert "<th>A</th><th>B</th>" in html
    assert "<td>1</td><td></td>" in html
    assert html.endswith("</table>")


def test_table_without_headers():
    assert "<th>" not in rich_table(None, [["x"]])


def test_kv_table_skips_none_values_and_bolds_keys():
    html = rich_kv_table([("Title", "Song"), ("Skipped", None)])
    assert "<td><b>Title</b></td><td>Song</td>" in html
    assert "Skipped" not in html


def test_details_closed_and_open():
    assert rich_details("S", "B") == "<details><summary>S</summary>B</details>"
    assert rich_details("S", "B", open=True).startswith("<details open>")


def test_sanitize_display_name():
    assert sanitize_display_name(None) == "User"
    assert sanitize_display_name("") == "User"
    assert sanitize_display_name("A\u200bB") == "AB"
    assert len(sanitize_display_name("x" * 200)) == 64
    assert sanitize_display_name("\u200b\u200b") == "User"


def test_sanitize_limits_stacked_combining_marks():
    zalgo = "a" + "\u0301" * 10
    assert sanitize_display_name(zalgo) == "a" + "\u0301" * 2
