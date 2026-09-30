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
    r"|button|img)(?=[\s/>])",
    re.I,
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


def rich_details(summary: str, body: str, open: bool = False) -> str:
    attr = " open" if open else ""
    return f"<details{attr}><summary>{summary}</summary>{body}</details>"


def rich_to_plain(html_text: str) -> str:
    if not html_text:
        return ""
    text = str(html_text)
    text = _EMOJI_TAG_RE.sub(r"\1", text)
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
    text = re.sub(r"<summary>(.*?)</summary>", r"<b>\1</b>\n", text, flags=re.I | re.S)
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
