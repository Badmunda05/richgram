# richgram

Telegram Bot API 10.3 rich messages for Pyrogram, Pyrofork and Kurigram bots:
tables, details, lists, colored buttons, drafts and ephemeral messages, with an
automatic plain-text fallback when a rich message is rejected.

## Install

```bash
pip install richgram
```

Or straight from GitHub:

```bash
pip install git+https://github.com/Badmunda05/richgram.git
```

## How to import

Import only what you need (recommended):

```python
from richgram import rich_send, rich_reply, rich_edit
from richgram import rich_heading, rich_note, rich_table, rich_kv_table
from richgram import rich_button, rich_button_row
```

Or import the whole package and use the `richgram.` prefix:

```python
import richgram

text = richgram.rich_heading("Hello", level=3)
await richgram.rich_send(client, chat_id, text)
```

Or import from the submodule directly:

```python
from richgram.rich_ui import rich_send, rich_button
```

Check the version and whether your build supports rich messages:

```python
import richgram

print(richgram.__version__)
print(richgram.RICH_AVAILABLE)
```

## Quick example

```python
from richgram import rich_send, rich_heading, rich_kv_table, rich_esc

text = (
    rich_heading("Now Playing", level=3)
    + rich_kv_table([
        ("Title", rich_esc("Song name")),
        ("Duration", "3:27"),
    ])
)

await rich_send(client, chat_id, text)
```

## Buttons

Buttons are part of the message HTML, so append them to the content
(there is no `reply_markup`):

```python
from richgram import rich_button, rich_button_row, rich_send

buttons = (
    rich_button_row(
        rich_button("Support", url="https://t.me/BadmundaXd", style="primary"),
        rich_button("Pause", callback_data="pause", style="success"),
    )
    + rich_button_row(rich_button("Close", callback_data="close", style="danger"))
)

await rich_send(client, chat_id, text + buttons)
```

- `style`: `primary` (blue), `success` (green), `danger` (red), `link`, or leave it out for grey.
- URL button: `type="url"` with `url="..."`.
- Callback button: `type="callback_data"` with `data="..."`.
- `rich_button_row(..., align="center")` aligns the row (`left`, `center`, `right`).

Random colours like an inline keyboard:

```python
import random

style = random.choice(["primary", "success", "danger"])
rich_button("Shuffle", callback_data="shuffle", style=style)
```

## Content blocks

```python
from richgram import (
    rich_heading, rich_note, rich_code, rich_pre, rich_list, rich_hr,
    rich_footer, rich_pull_quote, rich_math, rich_anchor, rich_thinking,
    rich_table, rich_kv_table, rich_details, rich_img, rich_esc,
)

rich_list(["one", "two"])
rich_list(["first", "second"], ordered=True)
rich_pre("print('hi')", language="python")
rich_math("x^2 + y^2 = z^2")
rich_details("More", "hidden text", open=True)
```

## Map, collage, slideshow, audio, video

These blocks are sent as typed Kurigram blocks with `rich_send_blocks`:

```python
from pyrogram.types import InputRichBlockMap
from richgram import rich_send_blocks

await rich_send_blocks(client, chat_id, [InputRichBlockMap(...)])
```

## Sending and editing

```python
from richgram import rich_reply, rich_edit, rich_edit_inline, rich_answer

msg = await rich_reply(message, text)
await rich_edit(msg, text + buttons)
await rich_edit(callback_query, text + buttons)
await rich_edit_inline(client, inline_message_id, text)
await rich_answer(callback_query, text)
```

Extra options on `rich_send`, `rich_reply` and `rich_edit`:

```python
await rich_send(
    client, chat_id, text,
    business_connection_id="...",
    direct_messages_topic_id=5,
    message_thread_id=9,
    allow_paid_broadcast=True,
    suggested_post_parameters=params,
    disable_notification=True,
    protect_content=True,
    effect_id=123,
    is_rtl=True,
    skip_entity_detection=True,
)
```

Markdown instead of HTML:

```python
await rich_send(client, chat_id, "# Title\n\n**bold** text", markdown=True)
```

## Ephemeral messages

```python
from richgram import rich_reply, ephemeral_edit, ephemeral_delete

sent = await rich_reply(message, text, ephemeral=True)
await ephemeral_edit(sent, new_text)
await ephemeral_delete(sent)
```

## Streaming drafts

```python
from richgram import RichDraft, rich_heading

async with RichDraft(client, chat_id, can_stop=True) as draft:
    await draft.update(rich_heading("Searching..."))
    await draft.finish(final_text)
```

## Fallback and debugging

If Telegram rejects a rich message, richgram sends a readable plain-text version
instead (buttons become links or bold text). To see why a rich message failed:

```python
import logging

logging.getLogger("richgram").setLevel(logging.DEBUG)
```

Transform HTML before it is sent (for example custom emoji):

```python
from richgram import add_html_hook

@add_html_hook
def custom_emoji(html):
    return html.replace(":fire:", '<emoji id="5368324170671202286">🔥</emoji>')
```

Plain-text helpers: `rich_to_plain(html)` and `rich_caption(html)`.

## Everything you can import

`RICH_AVAILABLE`, `rich_esc`, `sanitize_display_name`, `rich_heading`,
`rich_note`, `rich_table`, `rich_kv_table`, `rich_details`, `rich_code`,
`rich_pre`, `rich_list`, `rich_hr`, `rich_footer`, `rich_pull_quote`,
`rich_math`, `rich_anchor`, `rich_thinking`, `rich_img`, `rich_button`,
`rich_button_row`, `rich_to_plain`, `rich_caption`, `add_html_hook`,
`clear_html_hooks`, `rich_send`, `rich_send_blocks`, `rich_reply`,
`rich_edit`, `rich_edit_inline`, `rich_answer`, `ephemeral_edit`,
`ephemeral_delete`, `RichDraft`

## Demo bot

`bot.py` is a small demo bot (`/start` with shuffling button colours):

```bash
API_ID=123 API_HASH=abc BOT_TOKEN=123:xyz python bot.py
```

## Tests

```bash
pip install -e ".[test]"
pytest -m "unit or guard"
```

The unit tests use fake clients and messages, so they need no Telegram
connection. `tests/integrations` sends a real message when `API_ID`,
`API_HASH`, `BOT_TOKEN` and `CHAT_ID` are set.

## Used by

- [ShizuMusic](https://github.com/Badmunda05/ShizuMusic) Telegram music bot

## Requirements

- Python 3.10+
- A **Pyrogram / Pyrofork / Kurigram** build that has Bot API 10.3 rich message
  support (`InputRichMessage` and `Client.send_rich_message`).
  `RICH_AVAILABLE` is `True` when your build has it.

## Credits

- **[Kurigram](https://github.com/kurigram-org/kurigram)** for Bot API 10.3 rich message
  support in the Pyrogram ecosystem. Full credit to the Kurigram developers.
- richgram by [BadmundaXd](https://t.me/BadmundaXd).
