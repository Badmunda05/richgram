# richgram

Telegram Bot API 10.3 rich messages (tables, details, buttons, headings) for
Pyrogram / pyrofrok /Kurigram bots, with an automatic plain-text fallback.

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
from richgram import rich_details, rich_code, rich_esc
```

Or import the whole module and use the `richgram.` prefix:

```python
import richgram

text = richgram.rich_heading("Hello", level=3)
await richgram.rich_send(client, chat_id, text)
```

Or import from the submodule directly:

```python
from richgram.rich_ui import rich_send, rich_button
```

Check the version:

```python
import richgram
print(richgram.__version__)
```

## Quick example

```python
from richgram import (
    rich_send, rich_heading, rich_kv_table, rich_esc, RICH_AVAILABLE,
)

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
buttons = (
    "<tg-button-row>"
    '<tg-button type="url" style="primary" url="https://t.me/BadmundaXd">Support</tg-button>'
    '<tg-button type="callback_data" style="success" data="pause">II</tg-button>'
    "</tg-button-row>"
)

await rich_send(client, chat_id, text + buttons)
```

- `style`: `primary` (blue), `success` (green), `danger` (red), or leave it out for grey.
- URL button: `type="url"` with `url="..."`.
- Callback button: `type="callback_data"` with `data="..."`.

## Editing and replying

```python
from richgram import rich_edit, rich_reply

msg = await rich_reply(message, text)          # reply to a message
await rich_edit(msg, text + buttons)           # edit it later
```

## Everything you can import

`RICH_AVAILABLE`, `rich_esc`, `sanitize_display_name`, `rich_heading`,
`rich_note`, `rich_table`, `rich_kv_table`, `rich_details`, `rich_code`,
`rich_button`, `rich_to_plain`, `rich_caption`, `rich_send`,
`rich_send_blocks`, `rich_reply`, `rich_edit`, `rich_answer`,
`ephemeral_edit`, `ephemeral_delete`, `RichDraft`

## Requirements

- Python 3.8+
- A **Pyrogram / Pyrofork / Kurigram** build that has Bot API 10.3 rich message
  support (`InputRichMessage` and `Client.send_rich_message`).
  `RICH_AVAILABLE` is `True` when your build has it.

## Credits

- **[Kurigram](https://github.com/KurimuzonAkuma/kurigram)** by KurimuzonAkuma,
  for Bot API 10.3 rich message support in the Pyrogram ecosystem. Full credit to the Kurigram developers.
- richgram by [BadmundaXd](https://t.me/BadmundaXd).
