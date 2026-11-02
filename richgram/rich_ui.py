from __future__ import annotations

import html as _html
import logging
import re

from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import ReplyParameters

try:
    from pyrogram.types import InputRichMessage
except ImportError:
    InputRichMessage = None

try:
    from pyrogram.types import EphemeralMessageParameters
except ImportError:
    EphemeralMessageParameters = None

try:
    from pyrogram.types import RichTextCustomEmoji
except ImportError:
    RichTextCustomEmoji = None

try:
    from pyrogram.types import InputRichBlockDetails
except ImportError:
    InputRichBlockDetails = None

try:
    from pyrogram.types import InputRichBlockParagraph
except ImportError:
    InputRichBlockParagraph = None

logger = logging.getLogger("richgram")

__all__ = [
    "RICH_AVAILABLE",
    "rich_esc",
    "sanitize_display_name",
    "rich_heading",
    "rich_note",
    "rich_table",
    "rich_kv_table",
    "rich_details",
    "rich_details_group",
    "rich_details_nested",
    "rich_block_details",
    "rich_block_paragraph",
    "rich_code",
    "rich_pre",
    "rich_list",
    "rich_hr",
    "rich_footer",
    "rich_pull_quote",
    "rich_math",
    "rich_anchor",
    "rich_thinking",
    "rich_img",
    "rich_emoji",
    "rich_emoji_markdown",
    "rich_text_custom_emoji",
    "register_custom_emoji",
    "register_custom_emojis",
    "clear_custom_emojis",
    "custom_emoji_names",
    "rich_emoji_named",
    "expand_emoji_shortcodes",
    "fetch_custom_emoji",
    "rich_button",
    "rich_button_row",
    "rich_to_plain",
    "rich_caption",
    "add_html_hook",
    "clear_html_hooks",
    "rich_send",
    "rich_send_blocks",
    "rich_reply",
    "rich_edit",
    "rich_edit_inline",
    "rich_answer",
    "ephemeral_edit",
    "ephemeral_delete",
    "RichDraft",
]

try:
    from pyrogram import Client as _Client

    RICH_AVAILABLE = InputRichMessage is not None and hasattr(_Client, "send_rich_message")
except Exception:
    RICH_AVAILABLE = False


BUTTON_STYLES = ("primary", "success", "danger", "link", "default")

_RICH_ONLY_TAGS = (
    "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tr", "th", "td",
    "details", "summary", "mark", "sub", "sup",
    "ul", "ol", "li", "aside", "footer",
    "tg-button", "tg-button-row", "tg-math-block", "tg-collage", "tg-slideshow",
    "tg-map", "tg-document", "tg-thinking",
    "button",
)
_BLOCK_BREAK_RE = re.compile(
    r"</(?:h[1-6]|tr|details|summary|blockquote|table|pre|li|aside|footer|tg-button-row)>", re.I
)
_CELL_BREAK_RE = re.compile(r"</(?:th|td)>", re.I)
_EMOJI_TAG_RE = re.compile(
    r'<(?:tg-)?emoji\s+(?:emoji-)?id="[^"]*"\s*>(.*?)</(?:tg-)?emoji>', re.I | re.S
)
_ANY_TAG_RE = re.compile(r"<[^>]+>")
_RICH_TAGS_RE = re.compile(
    r"</?(?:h[1-6]|table|thead|tbody|tr|th|td|details|summary|mark|sub|sup|ul|ol|li|hr|aside|footer"
    r"|tg-button-row|tg-button|tg-math-block|tg-collage|tg-slideshow|tg-map|tg-document|tg-thinking"
    r"|tg-emoji|emoji|button|img)(?=[\s/>])",
    re.I,
)
_LEGACY_EMOJI_RE = re.compile(
    r'<emoji\s+id="([^"]*)"\s*>(.*?)</emoji>', re.I | re.S
)
_BUTTON_RE = re.compile(r"<tg-button\b([^>]*)>(.*?)</tg-button>", re.I | re.S)
_ATTR_RE = re.compile(r'([\w-]+)\s*=\s*"([^"]*)"')

_html_hooks = []


def add_html_hook(func):
    if func not in _html_hooks:
        _html_hooks.append(func)
    return func


def clear_html_hooks():
    _html_hooks.clear()


def _has_rich_only_tags(html_text) -> bool:
    if not html_text:
        return False
    return bool(_RICH_TAGS_RE.search(str(html_text)))


def rich_esc(value) -> str:
    if value is None:
        return ""
    return _html.escape(str(value), quote=False)


def _attr(value) -> str:
    return _html.escape(str(value), quote=True)


_INVISIBLE_RE = re.compile(
    "[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff\u00ad]"
)
_COMBINING_RE = re.compile(
    "[\u0300-\u036f\u1ab0-\u1aff\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]"
)


def sanitize_display_name(value, max_len: int = 64) -> str:
    if not value:
        return "User"
    text = _INVISIBLE_RE.sub("", str(value))
    out, run = [], 0
    for ch in text:
        if _COMBINING_RE.match(ch):
            run += 1
            if run > 2:
                continue
        else:
            run = 0
        out.append(ch)
    cleaned = "".join(out).strip()
    return cleaned[:max_len] or "User"


def rich_img(src: str) -> str:
    return f'<img src="{_attr(src)}" />' if src else ""


def rich_heading(text: str, level: int = 1) -> str:
    level = max(1, min(6, int(level)))
    return f"<h{level}>{text}</h{level}>"


def rich_note(text: str, expandable: bool = False) -> str:
    attr = " expandable" if expandable else ""
    return f"<blockquote{attr}>{text}</blockquote>"


def rich_code(value) -> str:
    return f"<code>{rich_esc(value)}</code>"


def rich_pre(value, language: str = None) -> str:
    body = rich_esc(value)
    if language:
        return f'<pre><code class="language-{_attr(language)}">{body}</code></pre>'
    return f"<pre>{body}</pre>"


def rich_list(items, ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    body = "".join(f"<li>{'' if item is None else item}</li>" for item in items or ())
    return f"<{tag}>{body}</{tag}>"


def rich_hr() -> str:
    return "<hr/>"


def rich_footer(text: str) -> str:
    return f"<footer>{text}</footer>"


def rich_pull_quote(text: str) -> str:
    return f"<aside>{text}</aside>"


def rich_math(expression: str) -> str:
    return f"<tg-math-block>{rich_esc(expression)}</tg-math-block>"


def rich_anchor(name: str) -> str:
    return f'<a name="{_attr(name)}"></a>'


def rich_thinking() -> str:
    return "<tg-thinking></tg-thinking>"


_MAX_CUSTOM_EMOJI_ID = 2**63 - 1


def _validate_custom_emoji_id(document_id) -> str:
    if isinstance(document_id, bool):
        raise ValueError("custom emoji id must be digits, not a boolean")
    if isinstance(document_id, int):
        value = document_id
    elif isinstance(document_id, str):
        text = document_id.strip()
        if not text.isdigit():
            raise ValueError(
                f"invalid custom emoji id {document_id!r}: expected digits only"
            )
        value = int(text)
    else:
        raise ValueError(
            f"invalid custom emoji id {document_id!r}: expected an int or a digit string"
        )
    if not 1 <= value <= _MAX_CUSTOM_EMOJI_ID:
        raise ValueError(
            f"invalid custom emoji id {document_id!r}: out of range 1..{_MAX_CUSTOM_EMOJI_ID}"
        )
    return str(value)


def _validate_emoji_alt(alt) -> str:
    if not isinstance(alt, str) or not alt.strip():
        raise ValueError(
            "custom emoji needs a non-empty alternative emoji, e.g. rich_emoji(id, '🔥')"
        )
    return alt.strip()


def rich_emoji(document_id, alt: str) -> str:
    """A premium custom emoji in Bot API HTML form.

    Example: ``rich_emoji("5368324170671202286", "🔥")`` ->
    ``<tg-emoji emoji-id="5368324170671202286">🔥</tg-emoji>``.

    ``document_id`` is the custom-emoji sticker's document id (not a
    file_id, pack name, or t.me/addemoji link). Read one off a message
    entity of type custom_emoji, a sticker set (``Sticker.custom_emoji_id``),
    or :func:`fetch_custom_emoji`. A fabricated id fails at send time, so
    the shape is validated here (digits only, fits in a signed 64-bit int).

    ``alt`` is the plain emoji shown where the custom emoji cannot be
    displayed (notifications, forwards by non-premium users, and richgram's
    plain-text fallback). It is required: Telegram requires a valid emoji
    as the content of the tag.

    Eligibility (Bot API 9.4+): a bot may send custom emoji if its owner
    has Telegram Premium (direct messages to private/group/supergroup
    chats) or if the bot purchased additional usernames on Fragment (also
    channels). richgram cannot check eligibility; an ineligible send is
    rejected by Telegram and :func:`rich_send` falls back to ``alt``.
    """
    emoji_id = _validate_custom_emoji_id(document_id)
    alt_text = _validate_emoji_alt(alt)
    return f'<tg-emoji emoji-id="{emoji_id}">{rich_esc(alt_text)}</tg-emoji>'


def rich_emoji_markdown(document_id, alt: str) -> str:
    """The same custom emoji in MarkdownV2 form: ``![alt](tg://emoji?id=...)``."""
    emoji_id = _validate_custom_emoji_id(document_id)
    alt_text = _validate_emoji_alt(alt)
    return f"![{alt_text}](tg://emoji?id={emoji_id})"


def rich_text_custom_emoji(document_id, alt: str):
    """A typed ``RichTextCustomEmoji`` for use in ``rich_send_blocks``.

    Example: ``InputRichBlockParagraph(text=[rich_text_custom_emoji(id, "🔥")])``.
    Requires a Kurigram build with ``RichTextCustomEmoji``.
    """
    if RichTextCustomEmoji is None:
        raise RuntimeError(
            "rich_text_custom_emoji needs a Kurigram build with RichTextCustomEmoji"
        )
    return RichTextCustomEmoji(
        custom_emoji_id=_validate_custom_emoji_id(document_id),
        alternative_text=_validate_emoji_alt(alt),
    )


async def fetch_custom_emoji(client, document_id):
    """Verify a custom emoji id and get its sticker (or ``None``).

    Calls ``client.get_custom_emoji_stickers([id])`` (at most 200 ids per
    call; this helper checks one). The returned sticker carries
    ``.custom_emoji_id`` and ``.emoji`` — the fallback glyph to pass as
    ``alt`` to :func:`rich_emoji`.
    """
    emoji_id = _validate_custom_emoji_id(document_id)
    getter = getattr(client, "get_custom_emoji_stickers", None)
    if getter is None:
        raise RuntimeError(
            "fetch_custom_emoji needs a client with get_custom_emoji_stickers "
            "(Kurigram / Pyrogram)"
        )
    stickers = await getter([emoji_id])
    if not stickers:
        return None
    return stickers[0]


_CUSTOM_EMOJI_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_SHORTCODE_RE = re.compile(r":([A-Za-z][A-Za-z0-9_-]*):")
_VERBATIM_SPLIT_RE = re.compile(
    r"(<(?:pre|code)\b[^>]*>.*?</(?:pre|code)>)", re.I | re.S
)

_custom_emojis: dict = {}


def _validate_custom_emoji_name(name) -> str:
    if not isinstance(name, str) or not _CUSTOM_EMOJI_NAME_RE.match(name.strip()):
        raise ValueError(
            f"invalid custom emoji name {name!r}: use letters, digits, '_' or '-', "
            "starting with a letter (e.g. 'fire')"
        )
    return name.strip().lower()


def register_custom_emoji(name, document_id, alt: str) -> str:
    """Register one custom emoji by name; returns its markup."""
    key = _validate_custom_emoji_name(name)
    emoji_id = _validate_custom_emoji_id(document_id)
    alt_text = _validate_emoji_alt(alt)
    _custom_emojis[key] = (emoji_id, alt_text)
    return rich_emoji(emoji_id, alt_text)


def register_custom_emojis(mapping) -> None:
    """Register many custom emojis at once.

    ``mapping`` is ``{name: (document_id, alt)}`` or
    ``{name: {"id": document_id, "alt": alt}}``.
    """
    for name, value in dict(mapping).items():
        if isinstance(value, dict):
            document_id, alt = value.get("id"), value.get("alt")
        else:
            document_id, alt = value
        register_custom_emoji(name, document_id, alt)


def clear_custom_emojis() -> None:
    _custom_emojis.clear()


def custom_emoji_names() -> list:
    return sorted(_custom_emojis)


def rich_emoji_named(name) -> str:
    """Markup for a registered custom emoji, by name."""
    key = _validate_custom_emoji_name(name)
    try:
        emoji_id, alt = _custom_emojis[key]
    except KeyError:
        known = ", ".join(custom_emoji_names()) or "(none registered)"
        raise KeyError(
            f"unknown custom emoji {name!r}; registered names: {known}"
        ) from None
    return rich_emoji(emoji_id, alt)


def expand_emoji_shortcodes(html_text: str) -> str:
    """Replace registered ``:name:`` shortcodes with custom-emoji markup.

    Register names first, e.g. ``register_custom_emoji("fire", id, "🔥")``,
    then use as an html hook so ``rich_send`` expands them on the way out::

        add_html_hook(expand_emoji_shortcodes)

    Only registered names expand; unknown shortcodes (and times like
    12:30) are left untouched. Shortcodes inside ``<pre>``/``<code>`` are
    never expanded, so code samples stay verbatim.
    """
    if not html_text or not _custom_emojis:
        return html_text or ""

    def _expand(segment: str) -> str:
        def _replace(match):
            key = match.group(1).lower()
            entry = _custom_emojis.get(key)
            if entry is None:
                return match.group(0)
            return rich_emoji(entry[0], entry[1])

        return _SHORTCODE_RE.sub(_replace, segment)

    parts = _VERBATIM_SPLIT_RE.split(str(html_text))
    for i in range(0, len(parts), 2):
        parts[i] = _expand(parts[i])
    return "".join(parts)


def rich_button(
    text: str,
    url: str = None,
    callback_data: str = None,
    style: str = None,
) -> str:
    style_attr = f' style="{_attr(style)}"' if style in BUTTON_STYLES else ""
    if callback_data:
        return (
            f'<tg-button type="callback_data"{style_attr} '
            f'data="{_attr(callback_data)}">{text}</tg-button>'
        )
    if url:
        return f'<tg-button type="url"{style_attr} url="{_attr(url)}">{text}</tg-button>'
    return f"<tg-button{style_attr}>{text}</tg-button>"


def rich_button_row(*buttons, align: str = None) -> str:
    if len(buttons) == 1 and isinstance(buttons[0], (list, tuple)):
        buttons = tuple(buttons[0])
    align_attr = f' align="{_attr(align)}"' if align in ("left", "center", "right") else ""
    return f"<tg-button-row{align_attr}>" + "".join(buttons) + "</tg-button-row>"


def rich_table(headers, rows, border: int = 1) -> str:
    parts = [f'<table border="{int(border)}">']
    if headers:
        cells = "".join(f"<th>{'' if h is None else h}</th>" for h in headers)
        parts.append(f"<tr>{cells}</tr>")
    for row in rows or ():
        cells = "".join(f"<td>{'' if c is None else c}</td>" for c in row)
        parts.append(f"<tr>{cells}</tr>")
    parts.append("</table>")
    return "".join(parts)


def rich_kv_table(pairs, headers=None, border: int = 1) -> str:
    rows = [
        (f"<b>{k}</b>", v)
        for k, v in (pairs or ())
        if v is not None
    ]
    return rich_table(headers, rows, border=border)


_MAX_DETAILS_DEPTH = 16
_DETAILS_TAG_RE = re.compile(r"<details\b[^>]*>|</details>", re.I)


def _max_details_depth(html_text: str) -> int:
    depth = 0
    deepest = 0
    for match in _DETAILS_TAG_RE.finditer(str(html_text or "")):
        if match.group(0).startswith("</"):
            depth = max(0, depth - 1)
        else:
            depth += 1
            deepest = max(deepest, depth)
    return deepest


def _validate_details_summary(summary) -> str:
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("a details section needs a non-empty summary string")
    return summary


def rich_details(summary: str, body: str, open: bool = False) -> str:
    """One collapsible section.

    Nesting is allowed: pass another ``rich_details(...)`` (or any HTML
    containing ``<details>``) as ``body``. Telegram allows up to 16 levels
    of nested formatting and blocks, so deeper nesting raises ValueError
    here instead of failing at send time.
    """
    if _max_details_depth(body) >= _MAX_DETAILS_DEPTH:
        raise ValueError(
            "nested details exceed Telegram's 16-level limit for rich messages"
        )
    attr = " open" if open else ""
    return f"<details{attr}><summary>{summary}</summary>{body}</details>"


def _details_section(section):
    """Normalise one group/nested section to (summary, body, open, children)."""
    children = ()
    if isinstance(section, dict):
        summary = section.get("summary")
        body = section.get("body", "")
        is_open = section.get("open", False)
        children = section.get("children", ())
    elif isinstance(section, (list, tuple)):
        if len(section) not in (2, 3):
            raise ValueError(
                "a details section is (summary, body) or (summary, body, open)"
            )
        summary, body = section[0], section[1]
        is_open = section[2] if len(section) == 3 else False
    else:
        raise ValueError(
            "a details section is a (summary, body) tuple or a dict with "
            "'summary' and 'body'"
        )
    summary = _validate_details_summary(summary)
    if body is None:
        body = ""
    if not isinstance(body, str):
        raise ValueError("a details body must be a string")
    if children is None:
        children = ()
    if not isinstance(children, (list, tuple)):
        raise ValueError("a details 'children' value must be a list of sections")
    return summary, body, bool(is_open), children


def rich_details_group(sections, *, open_first: bool = False, open_all: bool = False) -> str:
    """Several sibling collapsible sections in one message.

    ``sections`` is an iterable of ``(summary, body)``, ``(summary, body, open)``
    or ``{"summary": ..., "body": ..., "open": ...}``. A per-section ``open``
    wins over ``open_first``/``open_all``; ``open_first`` opens only the
    first section, ``open_all`` opens every section. Sections open and close
    independently: Telegram has no accordion mode. Returns "" for no sections.
    """
    if open_first and open_all:
        raise ValueError("open_first and open_all cannot both be True")
    parts = []
    for index, section in enumerate(sections or ()):
        summary, body, is_open, _children = _details_section(section)
        if not is_open:
            is_open = open_all or (open_first and index == 0)
        parts.append(rich_details(summary, body, open=is_open))
    return "\n".join(parts)


def _details_tree(node, depth: int) -> str:
    """Build one (possibly nested) details section from a node."""
    if isinstance(node, str):
        if _max_details_depth(node) + depth - 1 > _MAX_DETAILS_DEPTH:
            raise ValueError(
                "nested details exceed Telegram's 16-level limit for rich messages"
            )
        return node
    summary, body, is_open, children = _details_section(node)
    if depth > _MAX_DETAILS_DEPTH:
        raise ValueError(
            "nested details exceed Telegram's 16-level limit for rich messages"
        )
    inner = body + "".join(
        _details_tree(child, depth + 1) for child in (children or ())
    )
    return rich_details(summary, inner, open=is_open)


def rich_details_nested(summary: str, body: str = "", children=(), open: bool = False) -> str:
    """One collapsible section containing nested collapsible sections.

    ``children`` are sections in the same shapes ``rich_details_group``
    accepts, plus dicts with a ``children`` key for deeper nesting and
    prebuilt ``rich_details(...)`` strings. Example::

        rich_details_nested("Guide", "Start here.", children=[
            ("Install", "pip install richgram"),
            {"summary": "Advanced", "body": "", "children": [
                ("Source", "Clone the repo and read rich_ui.py"),
            ]},
        ])

    Nesting deeper than Telegram's 16 levels raises ValueError.
    """
    return _details_tree(
        {"summary": summary, "body": body, "open": open, "children": children},
        depth=1,
    )


def rich_block_paragraph(text: str):
    """A typed ``InputRichBlockParagraph`` for use in ``rich_send_blocks``."""
    if InputRichBlockParagraph is None:
        raise RuntimeError(
            "rich_block_paragraph needs a Kurigram build with InputRichBlockParagraph"
        )
    return InputRichBlockParagraph(text=text)


def rich_block_details(summary: str, blocks, open: bool = False):
    """A typed ``InputRichBlockDetails`` for use in ``rich_send_blocks``.

    ``blocks`` is a list of ``InputRichBlock`` objects; nest another
    ``rich_block_details(...)`` inside it for nested collapsibles.
    """
    if InputRichBlockDetails is None:
        raise RuntimeError(
            "rich_block_details needs a Kurigram build with InputRichBlockDetails"
        )
    return InputRichBlockDetails(
        summary=_validate_details_summary(summary),
        blocks=list(blocks or ()),
        is_open=True if open else None,
    )


_DETAILS_OUTLINE_RE = re.compile(
    r"<details\b[^>]*>|</details>|<summary>(.*?)</summary>", re.I | re.S
)


def _details_to_outline(html_text: str, bold: bool) -> str:
    depth = 0

    def _replace(match):
        nonlocal depth
        token = match.group(0)
        lowered = token.lower()
        if lowered.startswith("</details"):
            depth = max(0, depth - 1)
            return "\n"
        if lowered.startswith("<details"):
            depth += 1
            return ""
        summary = match.group(1) or ""
        indent = "  " * max(0, depth - 1)
        if bold:
            return f"{indent}▸ <b>{summary}</b>\n"
        return f"{indent}▸ {summary}\n"

    return _DETAILS_OUTLINE_RE.sub(_replace, html_text)


def rich_to_plain(html_text: str) -> str:
    if not html_text:
        return ""
    text = str(html_text)
    text = _EMOJI_TAG_RE.sub(r"\1", text)
    text = _details_to_outline(text, bold=False)
    text = re.sub(r"<li\b[^>]*>", "\u2022 ", text, flags=re.I)
    text = re.sub(r"<hr\s*/?>", "\n", text, flags=re.I)
    text = _CELL_BREAK_RE.sub("\x1f", text)
    text = _BLOCK_BREAK_RE.sub("\n", text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = _ANY_TAG_RE.sub("", text)
    text = _html.unescape(text)
    text = re.sub(r"\x1f+(?=\s*(?:\n|$))", "", text)
    text = text.replace("\x1f", " \u2022 ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def rich_caption(html_text: str) -> str:
    return _plain_fallback(html_text)


_VERBATIM_BLOCK_RE = re.compile(
    r'(<(?:table|pre)\b[\s\S]*?</(?:table|pre)>)', re.I
)
_BR_CONVERT_RE = re.compile(
    r'(?<!<br/>)(?<!<br>)(?<!</p>)(?<!</h2>)(?<!</h1>)(?<!</h3>)(?<!</h4>)(?<!</h5>)(?<!</h6>)'
    r'(?<!</blockquote>)(?<!</summary>)(?<!</details>)(?<!</table>)(?<!</pre>)(?<!</li>)'
    r'(?<!</ul>)(?<!</ol>)(?<!<hr/>)(?<!<hr>)(?<!</aside>)(?<!</footer>)(?<!</tg-button-row>)\n',
    re.I,
)


def _normalize_html(html_text: str) -> str:
    if not html_text:
        return ""
    text = str(html_text).replace("\r\n", "\n")
    for hook in _html_hooks:
        try:
            text = hook(text)
        except Exception as e:
            logger.debug(f"[_normalize_html] html hook skipped: {e}")
    text = re.sub(r"href='([^']*)'", r'href="\1"', text)
    text = re.sub(r'href=(?!["\'])([^\s">]+)', r'href="\1"', text)
    text = _LEGACY_EMOJI_RE.sub(r'<tg-emoji emoji-id="\1">\2</tg-emoji>', text)
    parts = _VERBATIM_BLOCK_RE.split(text)
    for i in range(0, len(parts), 2):
        if not parts[i]:
            continue
        if i > 0 and parts[i].startswith("\n"):
            leading_nl = ""
            content = parts[i]
            while content.startswith("\n"):
                leading_nl += "\n"
                content = content[1:]
            parts[i] = leading_nl + _BR_CONVERT_RE.sub("<br/>\n", content)
        else:
            parts[i] = _BR_CONVERT_RE.sub("<br/>\n", parts[i])
    return "".join(parts)


def _button_to_plain(match) -> str:
    attrs = dict(_ATTR_RE.findall(match.group(1)))
    label = match.group(2)
    url = attrs.get("url")
    if url:
        return f'<a href="{url}">{label}</a>'
    return f"<b>{label}</b>"


def _plain_fallback(html_text: str) -> str:
    if not html_text:
        return ""
    text = _normalize_html(html_text)
    text = re.sub(r"<img\b[^>]*/?>", "", text, flags=re.I)
    text = re.sub(r"<p\b[^>]*>", "", text, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<h[1-6]>(.*?)</h[1-6]>", r"\n<b>\1</b>\n", text, flags=re.I | re.S)
    text = _details_to_outline(text, bold=True)
    text = re.sub(r"<mark>(.*?)</mark>", r"<b>\1</b>", text, flags=re.I | re.S)
    text = re.sub(r"<tg-math-block>(.*?)</tg-math-block>", r"<code>\1</code>", text, flags=re.I | re.S)
    text = _BUTTON_RE.sub(_button_to_plain, text)
    text = re.sub(r"<button[^>]*>(.*?)</button>", r"<b>\1</b>", text, flags=re.I | re.S)
    text = re.sub(r"<li\b[^>]*>", "\u2022 ", text, flags=re.I)
    text = re.sub(r"</li>", "\n", text, flags=re.I)
    text = re.sub(r"<hr\s*/?>", "\n\u2500\u2500\u2500\u2500\u2500\n", text, flags=re.I)
    text = re.sub(r"</tg-button-row>", "\n", text, flags=re.I)
    text = _CELL_BREAK_RE.sub("  ", text)
    text = re.sub(r"</tr>", "\n", text, flags=re.I)
    text = re.sub(r"</table>", "\n", text, flags=re.I)
    text = re.sub(r'<a\s+name="[^"]*"\s*>\s*</a>', "", text, flags=re.I)
    text = re.sub(
        r"</?(?:%s)(?:\s[^>]*)?>" % "|".join(_RICH_ONLY_TAGS),
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"<br\s*/?>\n?", "\n", text, flags=re.I)
    text = re.sub(r"[ \t]{2,}", "  ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _input_rich(
    text: str,
    *,
    markdown: bool = False,
    is_rtl=None,
    skip_entity_detection=None,
    media=None,
):
    options = {}
    if is_rtl is not None:
        options["is_rtl"] = is_rtl
    if skip_entity_detection is not None:
        options["skip_entity_detection"] = skip_entity_detection
    if media:
        options["media"] = media
    if markdown:
        return InputRichMessage(markdown=text, **options)
    return InputRichMessage(html=_normalize_html(text), **options)


def _is_group(chat_type) -> bool:
    value = getattr(chat_type, "value", chat_type)
    return value in ("group", "supergroup")


def _only_set(**values) -> dict:
    return {k: v for k, v in values.items() if v is not None}


async def rich_send(
    client,
    chat_id,
    html_text: str,
    *,
    reply_markup=None,
    markup=None,
    receiver_user_id=None,
    callback_query_id=None,
    replace_callback_query_message=None,
    reply_to_message_id=None,
    reply_parameters=None,
    message_thread_id=None,
    direct_messages_topic_id=None,
    business_connection_id=None,
    allow_paid_broadcast=None,
    suggested_post_parameters=None,
    disable_notification=None,
    protect_content=None,
    effect_id=None,
    markdown: bool = False,
    is_rtl=None,
    skip_entity_detection=None,
    media=None,
    **kwargs,
):
    if reply_markup is None:
        reply_markup = markup

    if not html_text:
        return None

    if kwargs:
        logger.debug(f"[rich_send] ignoring unknown arguments: {sorted(kwargs)}")

    if reply_parameters is None and reply_to_message_id:
        reply_parameters = ReplyParameters(message_id=reply_to_message_id)

    ephemeral_message_parameters = None
    if receiver_user_id and EphemeralMessageParameters is not None:
        ephemeral_message_parameters = EphemeralMessageParameters(
            receiver_user_id=receiver_user_id,
            callback_query_id=callback_query_id,
            replace_callback_query_message=replace_callback_query_message,
        )

    shared = _only_set(
        reply_markup=reply_markup,
        ephemeral_message_parameters=ephemeral_message_parameters,
        reply_parameters=reply_parameters,
        message_thread_id=message_thread_id,
        direct_messages_topic_id=direct_messages_topic_id,
        business_connection_id=business_connection_id,
        allow_paid_broadcast=allow_paid_broadcast,
        suggested_post_parameters=suggested_post_parameters,
        disable_notification=disable_notification,
        protect_content=protect_content,
        effect_id=effect_id,
    )

    wants_rich = bool(
        markdown or receiver_user_id or media or _has_rich_only_tags(html_text)
    )
    if RICH_AVAILABLE and wants_rich:
        try:
            return await client.send_rich_message(
                chat_id=chat_id,
                rich_message=_input_rich(
                    html_text,
                    markdown=markdown,
                    is_rtl=is_rtl,
                    skip_entity_detection=skip_entity_detection,
                    media=media,
                ),
                **shared,
            )
        except Exception as e:
            logger.debug(f"[rich_send] rich delivery failed, falling back: {e}")

    try:
        if markdown:
            return await client.send_message(
                chat_id=chat_id,
                text=html_text,
                parse_mode=ParseMode.MARKDOWN,
                link_preview_options=None,
                **shared,
            )
        return await client.send_message(
            chat_id=chat_id,
            text=_plain_fallback(html_text),
            parse_mode=ParseMode.HTML,
            link_preview_options=None,
            **shared,
        )
    except Exception as e:
        logger.debug(f"[rich_send] plain send failed: {e}")
        return None


async def _send_blocks_via_http(client, chat_id, blocks, *, reply_markup, reply_parameters, receiver_user_id, media_file, token):
    import json
    import os

    import httpx
    from pyrogram import enums, types

    payload = {
        "chat_id": chat_id,
        "rich_message": {"blocks": blocks},
    }
    if receiver_user_id:
        payload["ephemeral_message_parameters"] = {"receiver_user_id": receiver_user_id}
    if reply_markup is not None and hasattr(reply_markup, "inline_keyboard"):
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    _only_set(
                        text=getattr(btn, "text", ""),
                        callback_data=getattr(btn, "callback_data", None),
                        url=getattr(btn, "url", None),
                        style=getattr(btn.style, "value", str(btn.style)) if getattr(btn, "style", None) else None,
                    )
                    for btn in row
                ]
                for row in reply_markup.inline_keyboard
            ]
        }
    if reply_parameters is not None and hasattr(reply_parameters, "message_id"):
        payload["reply_parameters"] = {"message_id": reply_parameters.message_id}

    endpoint = f"https://api.telegram.org/bot{token}/sendRichMessage"
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        has_local = bool(media_file and isinstance(media_file, str) and os.path.exists(media_file))
        if has_local:
            form_data = {
                "chat_id": str(chat_id),
                "rich_message": json.dumps(payload["rich_message"]),
            }
            for key in ("reply_markup", "reply_parameters", "ephemeral_message_parameters"):
                if key in payload:
                    form_data[key] = json.dumps(payload[key])
            with open(media_file, "rb") as f:
                files = {"thumb": (os.path.basename(media_file), f.read(), "image/jpeg")}
            resp = await http_client.post(endpoint, data=form_data, files=files)
        else:
            resp = await http_client.post(endpoint, json=payload)

        if resp.status_code != 200 and any(
            isinstance(b, dict) and b.get("type") == "photo" for b in blocks
        ):
            payload["rich_message"]["blocks"] = [
                b for b in blocks if isinstance(b, dict) and b.get("type") != "photo"
            ]
            resp = await http_client.post(endpoint, json=payload)

        if resp.status_code != 200:
            logger.warning(f"[rich_send_blocks] Bot API {resp.status_code}: {resp.text}")
            return None
        data = resp.json()
        if not data.get("ok"):
            return None
        peer_id = chat_id if isinstance(chat_id, int) else 0
        return types.Message(
            id=data["result"]["message_id"],
            chat=types.Chat(id=peer_id, type=enums.ChatType.SUPERGROUP, client=client),
            reply_markup=reply_markup,
            client=client,
        )


async def rich_send_blocks(
    client,
    chat_id,
    blocks: list,
    *,
    reply_markup=None,
    reply_parameters=None,
    receiver_user_id=None,
    callback_query_id=None,
    replace_callback_query_message=None,
    message_thread_id=None,
    direct_messages_topic_id=None,
    business_connection_id=None,
    allow_paid_broadcast=None,
    suggested_post_parameters=None,
    disable_notification=None,
    protect_content=None,
    effect_id=None,
    is_rtl=None,
    skip_entity_detection=None,
    media_file=None,
    token=None,
):
    if not blocks:
        return None

    if any(isinstance(b, dict) for b in blocks):
        token = token or getattr(client, "bot_token", None)
        if not token:
            logger.debug("[rich_send_blocks] dict blocks need a bot token")
            return None
        try:
            return await _send_blocks_via_http(
                client,
                chat_id,
                blocks,
                reply_markup=reply_markup,
                reply_parameters=reply_parameters,
                receiver_user_id=receiver_user_id,
                media_file=media_file,
                token=token,
            )
        except Exception as e:
            logger.debug(f"[rich_send_blocks] direct Bot API block send failed: {e}")
            return None

    if not RICH_AVAILABLE:
        return None

    ephemeral_message_parameters = None
    if receiver_user_id and EphemeralMessageParameters is not None:
        ephemeral_message_parameters = EphemeralMessageParameters(
            receiver_user_id=receiver_user_id,
            callback_query_id=callback_query_id,
            replace_callback_query_message=replace_callback_query_message,
        )

    options = _only_set(is_rtl=is_rtl, skip_entity_detection=skip_entity_detection)
    try:
        return await client.send_rich_message(
            chat_id=chat_id,
            rich_message=InputRichMessage(blocks=list(blocks), **options),
            **_only_set(
                reply_markup=reply_markup,
                ephemeral_message_parameters=ephemeral_message_parameters,
                reply_parameters=reply_parameters,
                message_thread_id=message_thread_id,
                direct_messages_topic_id=direct_messages_topic_id,
                business_connection_id=business_connection_id,
                allow_paid_broadcast=allow_paid_broadcast,
                suggested_post_parameters=suggested_post_parameters,
                disable_notification=disable_notification,
                protect_content=protect_content,
                effect_id=effect_id,
            ),
        )
    except Exception as e:
        logger.warning(f"[rich_send_blocks] block send failed: {e}")
        return None


async def rich_reply(
    message,
    html_text: str,
    *,
    reply_markup=None,
    markup=None,
    ephemeral: bool = False,
    quote: bool = True,
    client=None,
    **kwargs,
):
    if reply_markup is None:
        reply_markup = markup

    if not html_text:
        return None

    if hasattr(message, "data") and hasattr(message, "message"):
        app = client or getattr(message, "_client", None)
        cb_user = getattr(message, "from_user", None)
        inner_msg = getattr(message, "message", None)
        chat = getattr(inner_msg, "chat", None)
        if not chat:
            return None
        receiver_user_id = cb_user.id if (ephemeral and cb_user and _is_group(chat.type)) else None
        return await rich_send(
            app,
            chat.id,
            html_text,
            reply_markup=reply_markup,
            receiver_user_id=receiver_user_id,
            reply_to_message_id=getattr(inner_msg, "id", None) if quote else None,
            message_thread_id=getattr(inner_msg, "message_thread_id", None),
            **kwargs,
        )

    chat = getattr(message, "chat", None)
    if not chat:
        return None
    app = client or getattr(message, "_client", None)
    from_user = getattr(message, "from_user", None)
    receiver_user_id = from_user.id if (ephemeral and from_user and _is_group(chat.type)) else None

    reply_parameters = None
    if quote and not receiver_user_id:
        ephemeral_id = getattr(message, "ephemeral_message_id", None)
        if ephemeral_id:
            reply_parameters = ReplyParameters(ephemeral_message_id=ephemeral_id)
        elif getattr(message, "id", 0):
            reply_parameters = ReplyParameters(message_id=message.id)

    return await rich_send(
        app,
        chat.id,
        html_text,
        reply_markup=reply_markup,
        receiver_user_id=receiver_user_id,
        reply_parameters=reply_parameters,
        message_thread_id=getattr(message, "message_thread_id", None),
        **kwargs,
    )


async def rich_edit(
    target,
    html_text: str,
    *,
    reply_markup=None,
    markup=None,
    chat_id=None,
    message_id=None,
    client=None,
    business_connection_id=None,
    markdown: bool = False,
    is_rtl=None,
    skip_entity_detection=None,
    media=None,
    **kwargs,
):
    if reply_markup is None:
        reply_markup = markup
    if not html_text:
        return None

    options = dict(
        business_connection_id=business_connection_id,
        markdown=markdown,
        is_rtl=is_rtl,
        skip_entity_detection=skip_entity_detection,
        media=media,
    )

    if hasattr(target, "data") and hasattr(target, "message"):
        app = client or getattr(target, "_client", None)
        msg = getattr(target, "message", None)
        inline_id = getattr(target, "inline_message_id", None)
        if msg is None and inline_id and app is not None:
            return await rich_edit_inline(
                app, inline_id, html_text, reply_markup=reply_markup, markdown=markdown,
                is_rtl=is_rtl, skip_entity_detection=skip_entity_detection, media=media,
            )
        if msg and hasattr(msg, "chat") and hasattr(msg, "id"):
            chat_id = msg.chat.id
            message_id = msg.id
        if app is not None and chat_id and message_id:
            return await _rich_edit_via_client(
                app, chat_id, message_id, html_text, reply_markup, **options
            )
        try:
            return await target.edit_message_text(
                _plain_fallback(html_text), parse_mode=ParseMode.HTML, reply_markup=reply_markup
            )
        except Exception as e:
            logger.debug(f"[rich_edit] cq plain edit failed: {e}")
            return None

    if hasattr(target, "chat") and hasattr(target, "id"):
        app = client or getattr(target, "_client", None)
        chat_id = target.chat.id
        message_id = target.id
        if app is not None:
            return await _rich_edit_via_client(
                app, chat_id, message_id, html_text, reply_markup, **options
            )
        try:
            return await target.edit_text(
                _plain_fallback(html_text),
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                link_preview_options=None,
            )
        except Exception as e:
            logger.debug(f"[rich_edit] message plain edit failed: {e}")
            return None

    return await _rich_edit_via_client(
        target, chat_id, message_id, html_text, reply_markup, **options
    )


async def _rich_edit_via_client(
    app,
    chat_id,
    message_id,
    html_text,
    reply_markup,
    *,
    business_connection_id=None,
    markdown: bool = False,
    is_rtl=None,
    skip_entity_detection=None,
    media=None,
):
    if chat_id is None or not message_id:
        logger.debug("[rich_edit] missing chat_id/message_id")
        return None

    extra = _only_set(business_connection_id=business_connection_id)
    wants_rich = bool(markdown or media or _has_rich_only_tags(html_text))

    if RICH_AVAILABLE and wants_rich:
        try:
            return await app.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                rich_message=_input_rich(
                    html_text,
                    markdown=markdown,
                    is_rtl=is_rtl,
                    skip_entity_detection=skip_entity_detection,
                    media=media,
                ),
                reply_markup=reply_markup,
                **extra,
            )
        except MessageNotModified:
            return None
        except Exception as e:
            logger.debug(f"[rich_edit] rich edit_message_text failed, falling back: {e}")

    try:
        if markdown:
            return await app.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=html_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
                link_preview_options=None,
                **extra,
            )
        return await app.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=_plain_fallback(html_text),
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            link_preview_options=None,
            **extra,
        )
    except MessageNotModified:
        return None
    except Exception as e:
        logger.debug(f"[rich_edit] plain edit failed: {e}")
        return None


async def rich_edit_inline(
    client,
    inline_message_id: str,
    html_text: str,
    *,
    reply_markup=None,
    markdown: bool = False,
    is_rtl=None,
    skip_entity_detection=None,
    media=None,
):
    if not html_text or not inline_message_id:
        return None

    wants_rich = bool(markdown or media or _has_rich_only_tags(html_text))
    if RICH_AVAILABLE and wants_rich:
        try:
            return await client.edit_inline_text(
                inline_message_id=inline_message_id,
                rich_message=_input_rich(
                    html_text,
                    markdown=markdown,
                    is_rtl=is_rtl,
                    skip_entity_detection=skip_entity_detection,
                    media=media,
                ),
                reply_markup=reply_markup,
            )
        except MessageNotModified:
            return None
        except Exception as e:
            logger.debug(f"[rich_edit_inline] rich edit failed, falling back: {e}")

    try:
        return await client.edit_inline_text(
            inline_message_id=inline_message_id,
            text=_plain_fallback(html_text),
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            link_preview_options=None,
        )
    except MessageNotModified:
        return None
    except Exception as e:
        logger.debug(f"[rich_edit_inline] plain edit failed: {e}")
        return None


async def rich_answer(
    callback_query,
    html_text: str,
    *,
    reply_markup=None,
    client=None,
):
    if not html_text:
        return None

    app = client or getattr(callback_query, "_client", None)
    message = getattr(callback_query, "message", None)
    chat = getattr(message, "chat", None)
    user = getattr(callback_query, "from_user", None)
    if app is None or chat is None:
        return None

    receiver_user_id = user.id if (user and _is_group(getattr(chat, "type", None))) else None
    return await rich_send(
        app,
        chat.id,
        html_text,
        reply_markup=reply_markup,
        receiver_user_id=receiver_user_id,
        callback_query_id=getattr(callback_query, "id", None) if receiver_user_id else None,
        message_thread_id=getattr(message, "message_thread_id", None),
    )


def _ephemeral_receiver(message):
    eph_id = getattr(message, "ephemeral_message_id", None)
    if not eph_id:
        return None
    chat = getattr(message, "chat", None)
    receiver = getattr(message, "receiver_user", None) or getattr(message, "from_user", None)
    receiver_id = getattr(receiver, "id", None)
    if chat is None or not receiver_id:
        return None
    return chat.id, receiver_id, eph_id


async def ephemeral_edit(message, html_text: str, *, reply_markup=None, client=None):
    if not html_text:
        return None
    target = _ephemeral_receiver(message)
    if target is None:
        return await rich_edit(message, html_text, reply_markup=reply_markup, client=client)

    app = client or getattr(message, "_client", None)
    if app is None:
        return None
    chat_id, receiver_id, eph_id = target
    base = dict(
        chat_id=chat_id,
        receiver_user_id=receiver_id,
        ephemeral_message_id=eph_id,
        reply_markup=reply_markup,
    )

    if RICH_AVAILABLE and _has_rich_only_tags(html_text):
        try:
            return await app.edit_ephemeral_message_text(
                rich_message=_input_rich(html_text), **base
            )
        except Exception as e:
            logger.debug(f"[ephemeral_edit] rich edit failed, falling back: {e}")

    try:
        return await app.edit_ephemeral_message_text(
            text=rich_caption(html_text), parse_mode=ParseMode.HTML, **base
        )
    except Exception as e:
        logger.debug(f"[ephemeral_edit] failed: {e}")
        return None


async def ephemeral_delete(message, *, client=None) -> bool:
    if message is None:
        return False
    target = _ephemeral_receiver(message)
    app = client or getattr(message, "_client", None)
    if target is None:
        try:
            await message.delete()
            return True
        except Exception as e:
            logger.debug(f"[ephemeral_delete] plain delete failed: {e}")
            return False

    if app is None:
        return False
    chat_id, receiver_id, eph_id = target
    try:
        await app.delete_ephemeral_message(
            chat_id=chat_id,
            receiver_user_id=receiver_id,
            ephemeral_message_id=eph_id,
        )
        return True
    except Exception as e:
        logger.debug(f"[ephemeral_delete] failed: {e}")
        return False


class RichDraft:
    __slots__ = (
        "client", "chat_id", "message_thread_id", "draft_id", "can_stop", "keep_on_stop",
        "_last_html", "_finished", "_result", "_drafts_ok",
    )

    def __init__(
        self,
        client,
        chat_id,
        *,
        message_thread_id=None,
        draft_id=None,
        can_stop=None,
        keep_on_stop=None,
    ):
        self.client = client
        self.chat_id = chat_id
        self.message_thread_id = message_thread_id
        self.draft_id = draft_id or self._new_id(client)
        self.can_stop = can_stop
        self.keep_on_stop = keep_on_stop
        self._last_html = None
        self._finished = False
        self._result = None
        self._drafts_ok = RICH_AVAILABLE and hasattr(client, "send_rich_message_draft")

    @staticmethod
    def _new_id(client):
        try:
            value = client.rnd_id()
        except Exception:
            import random

            value = random.getrandbits(63)
        return value or 1

    async def update(self, html_text: str) -> bool:
        if not html_text:
            return False
        self._last_html = html_text
        if not self._drafts_ok:
            return False
        try:
            await self.client.send_rich_message_draft(
                chat_id=self.chat_id,
                draft_id=self.draft_id,
                rich_message=_input_rich(html_text),
                **_only_set(
                    message_thread_id=self.message_thread_id,
                    can_stop=self.can_stop,
                    keep_on_stop=self.keep_on_stop,
                ),
            )
            return True
        except Exception as e:
            logger.debug(f"[RichDraft] draft update failed, disabling drafts: {e}")
            self._drafts_ok = False
            return False

    async def finish(self, html_text: str = None, *, reply_markup=None, **kwargs):
        self._finished = True
        final_html = html_text or self._last_html
        if not final_html:
            return None
        self._result = await rich_send(
            self.client,
            self.chat_id,
            final_html,
            reply_markup=reply_markup,
            message_thread_id=self.message_thread_id,
            **kwargs,
        )
        return self._result

    @property
    def result(self):
        return self._result

    def discard(self) -> None:
        self._finished = True
        self._last_html = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if not self._finished and exc_type is None:
            await self.finish()
        return False
