"""richgram: Telegram Bot API 10.3 rich messages for Pyrogram, Pyrofork and Kurigram bots."""

from . import rich_ui
from .rich_ui import *
from .rich_ui import __all__ as _rich_all

__version__ = "0.2.0"
__all__ = list(_rich_all) + ["rich_ui", "__version__"]
