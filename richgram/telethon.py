"""richgram Telethon transport: Bot API 10.3 rich messages over MTProto.

Pyrogram/Kurigram send rich messages through ``Client.send_rich_message``.
Telethon has no such method, but the same rich payload travels over MTProto
as a native request: ``messages.SendMessageRequest`` /
``messages.EditMessageRequest`` with ``rich_message`` set to a
``types.InputRichMessageHTML`` / ``InputRichMessageMarkdown`` /
``types.InputRichMessage`` (blocks). The TL schema still requires the
ordinary ``message`` field alongside the rich payload, so the adapter fills
it with the same rich source text; it is not a second transport.

This module is optional: ``telethon`` is an extra (``pip install
richgram[telethon]``) and importing ``richgram`` never requires it. All
HTML builders (``rich_heading``, ``rich_table``, ``rich_details``,
``rich_emoji``, ...) are transport-independent, so the same text works on
both transports; only the block objects differ (Telethon uses
``PageBlock*`` types, Pyrogram uses ``InputRichBlock*`` types).

On failure the adapter falls back to a plain Telethon ``send_message`` /
``edit_message`` with the rich HTML converted by ``_plain_fallback``,
mirroring ``rich_send``. Telethon's own HTML parser understands
``<tg-emoji>``, so premium emoji survive the plain path too.
"""
from __future__ import annotations

import logging

from .rich_ui import (
    _has_rich_only_tags,
    _normalize_html,
    _only_set,
    _plain_fallback,
    _todo_items,
)

logger = logging.getLogger("richgram.telethon")

__all__ = [
    "TELETHON_RICH_AVAILABLE",
    "telethon_input_rich",
    "telethon_send_request",
    "telethon_edit_request",
    "telethon_block_paragraph",
    "telethon_block_details",
    "telethon_block_todo_list",
    "telethon_rich_send",
    "telethon_rich_send_blocks",
    "telethon_rich_reply",
    "telethon_rich_edit",
]


def _load_telethon():
    """Return Telethon's (types, functions), or raise RuntimeError."""
    try:
        from telethon import functions, types
    except ImportError as exc:
        raise RuntimeError(
            "Telethon support needs telethon installed: pip install richgram[telethon]"
        ) from exc
    if not hasattr(types, "InputRichMessageHTML") or not hasattr(
        functions.messages, "SendMessageRequest"
    ):
        raise RuntimeError(
            "Telethon support needs a Telethon build with rich-message types "
            "(InputRichMessageHTML, SendMessageRequest with rich_message); "
            "telethon>=1.45 is known to work"
        )
    return types, functions


try:
    _load_telethon()
    TELETHON_RICH_AVAILABLE = True
except RuntimeError:
    TELETHON_RICH_AVAILABLE = False


def _require_telethon():
    return _load_telethon()


def telethon_input_rich(html_text: str, *, markdown: bool = False,
                        is_rtl=None, skip_entity_detection=None):
    """Build a Telethon ``InputRichMessage`` from HTML or Markdown text.

    HTML is normalised the same way ``rich_send`` normalises it (legacy
    ``<emoji id>`` becomes ``<tg-emoji emoji-id>``, newlines outside
    verbatim blocks become ``<br/>``).
    """
    types, _functions = _require_telethon()
    if not html_text:
        raise ValueError("telethon_input_rich needs non-empty text")
    options = _only_set(is_rtl=is_rtl, skip_entity_detection=skip_entity_detection)
    if markdown:
        return types.InputRichMessageMarkdown(markdown=html_text, **options)
    return types.InputRichMessageHTML(html=_normalize_html(html_text), **options)


def _reply_header(reply_to_msg_id, top_msg_id):
    if reply_to_msg_id is None:
        return None
    types, _functions = _require_telethon()
    return types.InputReplyToMessage(
        reply_to_msg_id=int(reply_to_msg_id),
        top_msg_id=int(top_msg_id) if top_msg_id is not None else None,
    )


def telethon_send_request(peer, html_text: str, *, markdown: bool = False,
                         reply_to_msg_id=None, top_msg_id=None,
                         reply_markup=None, silent=None, no_webpage=None,
                         is_rtl=None, skip_entity_detection=None):
    """Build a raw ``messages.SendMessageRequest`` carrying a rich message.

    ``peer`` is passed through untouched: Telethon resolves ints, usernames
    and ``InputPeer`` values itself when the request is invoked
    (``client(request)``), and it generates ``random_id`` when it is absent.
    """
    _types, functions = _require_telethon()
    if not html_text:
        raise ValueError("telethon_send_request needs non-empty text")
    rich_message = telethon_input_rich(
        html_text, markdown=markdown, is_rtl=is_rtl,
        skip_entity_detection=skip_entity_detection,
    )
    companion = (
        html_text if markdown else _normalize_html(html_text)
    ) or " "
    return functions.messages.SendMessageRequest(
        peer=peer,
        message=companion,
        no_webpage=no_webpage,
        silent=silent,
        reply_to=_reply_header(reply_to_msg_id, top_msg_id),
        reply_markup=reply_markup,
        rich_message=rich_message,
    )


def telethon_edit_request(peer, message_id: int, html_text: str, *,
                         markdown: bool = False, reply_markup=None,
                         no_webpage=None, is_rtl=None,
                         skip_entity_detection=None):
    """Build a raw ``messages.EditMessageRequest`` carrying a rich message."""
    _types, functions = _require_telethon()
    if not html_text:
        raise ValueError("telethon_edit_request needs non-empty text")
    rich_message = telethon_input_rich(
        html_text, markdown=markdown, is_rtl=is_rtl,
        skip_entity_detection=skip_entity_detection,
    )
    companion = (
        html_text if markdown else _normalize_html(html_text)
    ) or " "
    return functions.messages.EditMessageRequest(
        peer=peer,
        id=int(message_id),
        message=companion,
        no_webpage=no_webpage,
        reply_markup=reply_markup,
        rich_message=rich_message,
    )


def telethon_block_paragraph(text: str):
    """A Telethon ``PageBlockParagraph`` for use in ``telethon_rich_send_blocks``."""
    types, _functions = _require_telethon()
    return types.PageBlockParagraph(text=text)


def telethon_block_details(title: str, blocks, open: bool = False):
    """A Telethon ``PageBlockDetails`` for use in ``telethon_rich_send_blocks``.

    ``blocks`` is a list of Telethon ``PageBlock`` objects; nest another
    ``telethon_block_details(...)`` inside it for nested collapsibles.
    Note the argument order differs from Pyrogram's
    ``InputRichBlockDetails(summary, blocks)``: Telethon's constructor is
    ``PageBlockDetails(blocks, title, open)``.
    """
    types, _functions = _require_telethon()
    if not isinstance(title, str) or not title.strip():
        raise ValueError("a details block needs a non-empty title string")
    return types.PageBlockDetails(
        blocks=list(blocks or ()),
        title=title,
        open=True if open else None,
    )


def telethon_block_todo_list(items):
    """A Telethon checklist block for use in ``telethon_rich_send_blocks``.

    Builds a ``PageBlockList`` of ``PageListItemText`` items carrying
    ``checkbox`` and ``checked`` — the Telethon form of the same native
    checkboxes ``rich_todo_list`` and ``rich_block_todo_list`` produce.
    """
    types, _functions = _require_telethon()
    return types.PageBlockList(
        items=[
            types.PageListItemText(text=text, checkbox=True, checked=done)
            for text, done in _todo_items(items)
        ]
    )


async def telethon_rich_send_blocks(client, chat, blocks, *,
                                   reply_to_msg_id=None, top_msg_id=None,
                                   reply_markup=None, silent=None,
                                   no_webpage=None):
    """Send Telethon ``PageBlock`` objects as one rich message.

    Returns the invoked result, or ``None`` when there are no blocks or the
    rich request fails. Blocks have no plain-text equivalent, so unlike
    ``telethon_rich_send`` there is no plain fallback here.
    """
    if not blocks:
        return None
    types, functions = _require_telethon()
    try:
        request = functions.messages.SendMessageRequest(
            peer=chat,
            message=" ",
            no_webpage=no_webpage,
            silent=silent,
            reply_to=_reply_header(reply_to_msg_id, top_msg_id),
            reply_markup=reply_markup,
            rich_message=types.InputRichMessage(blocks=list(blocks)),
        )
        return await client(request)
    except Exception as e:
        logger.warning(f"[telethon_rich_send_blocks] block send failed: {e}")
        return None


async def telethon_rich_send(client, chat, html_text: str, *,
                            reply_to_msg_id=None, top_msg_id=None,
                            reply_markup=None, silent=None, no_webpage=None,
                            markdown: bool = False, is_rtl=None,
                            skip_entity_detection=None, **kwargs):
    """Send rich HTML/Markdown with a Telethon client, falling back to plain.

    Rich content goes out as a raw ``SendMessageRequest`` with
    ``rich_message`` set. Plain text (no rich-only tags, no markdown) and
    any rich request Telegram rejects go out as an ordinary Telethon
    ``send_message`` with ``parse_mode="html"`` and the plain fallback text.
    """
    if not html_text:
        return None
    if kwargs:
        logger.debug(f"[telethon_rich_send] ignoring unknown arguments: {sorted(kwargs)}")

    wants_rich = bool(
        markdown or _has_rich_only_tags(html_text)
    )
    if TELETHON_RICH_AVAILABLE and wants_rich:
        try:
            request = telethon_send_request(
                chat, html_text, markdown=markdown,
                reply_to_msg_id=reply_to_msg_id, top_msg_id=top_msg_id,
                reply_markup=reply_markup, silent=silent, no_webpage=no_webpage,
                is_rtl=is_rtl, skip_entity_detection=skip_entity_detection,
            )
            return await client(request)
        except Exception as e:
            logger.debug(f"[telethon_rich_send] rich delivery failed, falling back: {e}")

    try:
        return await client.send_message(
            chat,
            _plain_fallback(html_text) if not markdown else html_text,
            parse_mode="html" if not markdown else "md",
            reply_to=int(reply_to_msg_id) if reply_to_msg_id is not None else None,
            reply_markup=reply_markup,
            silent=silent,
            link_preview=False if no_webpage else None,
        )
    except Exception as e:
        logger.debug(f"[telethon_rich_send] plain send failed: {e}")
        return None


async def telethon_rich_reply(message, html_text: str, *, client=None,
                             **kwargs):
    """Reply to a Telethon message (or callback query) with rich text."""
    if not html_text:
        return None

    if hasattr(message, "data") and hasattr(message, "message"):
        inner = getattr(message, "message", None)
        chat = getattr(inner, "chat_id", None) if inner is not None else None
        reply_to = getattr(inner, "id", None) if inner is not None else None
        app = client or getattr(message, "client", None) or getattr(
            message, "_client", None
        )
    else:
        chat = getattr(message, "chat_id", None)
        reply_to = getattr(message, "id", None)
        app = (
            client or getattr(message, "client", None)
            or getattr(message, "_client", None)
        )
    if app is None or chat is None or reply_to is None:
        return None
    return await telethon_rich_send(
        app, chat, html_text, reply_to_msg_id=reply_to, **kwargs
    )


async def telethon_rich_edit(target, html_text: str, *, client=None,
                            chat=None, message_id=None, **kwargs):
    """Edit a message to rich text with a Telethon client.

    ``target`` is a Telethon message (``.chat_id`` / ``.id``) or a client,
    in which case ``chat`` and ``message_id`` are required.
    """
    if not html_text:
        return None

    if hasattr(target, "chat_id") and hasattr(target, "id"):
        app = client or getattr(target, "client", None) or getattr(
            target, "_client", None
        )
        chat = target.chat_id
        message_id = target.id
    else:
        app = client or target
    if app is None or chat is None or message_id is None:
        logger.debug("[telethon_rich_edit] missing client/chat/message_id")
        return None

    markdown = kwargs.pop("markdown", False)
    is_rtl = kwargs.pop("is_rtl", None)
    skip_entity_detection = kwargs.pop("skip_entity_detection", None)
    reply_markup = kwargs.pop("reply_markup", None)
    no_webpage = kwargs.pop("no_webpage", None)
    if kwargs:
        logger.debug(f"[telethon_rich_edit] ignoring unknown arguments: {sorted(kwargs)}")

    wants_rich = bool(markdown or _has_rich_only_tags(html_text))
    if TELETHON_RICH_AVAILABLE and wants_rich:
        try:
            request = telethon_edit_request(
                chat, message_id, html_text, markdown=markdown,
                reply_markup=reply_markup, no_webpage=no_webpage,
                is_rtl=is_rtl, skip_entity_detection=skip_entity_detection,
            )
            return await app(request)
        except Exception as e:
            logger.debug(f"[telethon_rich_edit] rich edit failed, falling back: {e}")

    try:
        return await app.edit_message(
            chat,
            message_id,
            _plain_fallback(html_text) if not markdown else html_text,
            parse_mode="html" if not markdown else "md",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.debug(f"[telethon_rich_edit] plain edit failed: {e}")
        return None
