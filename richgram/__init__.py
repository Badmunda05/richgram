"""richgram — Telegram Bot API 10.3 rich messages for Pyrogram/pyrofrok/Kurigram bots."""

from .rich_ui import *  # noqa: F401,F403
from .rich_ui import __all__ as _rich_all

__version__ = "0.1.0"
__all__ = list(_rich_all) + ["__version__"]
