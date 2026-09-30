import enum
import sys
import types


def install_if_missing() -> bool:
    try:
        import pyrogram
        from pyrogram.types import InputRichMessage
        return False
    except ImportError:
        pass

    for name in list(sys.modules):
        if name == "pyrogram" or name.startswith("pyrogram."):
            del sys.modules[name]

    pyrogram = types.ModuleType("pyrogram")
    enums = types.ModuleType("pyrogram.enums")
    errors = types.ModuleType("pyrogram.errors")
    pytypes = types.ModuleType("pyrogram.types")

    class ParseMode(enum.Enum):
        HTML = "html"
        MARKDOWN = "markdown"

    class MessageNotModified(Exception):
        pass

    class _Obj:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class InputRichMessage(_Obj):
        def __init__(self, blocks=None, html=None, markdown=None, media=None,
                     is_rtl=None, skip_entity_detection=None):
            super().__init__(
                blocks=blocks, html=html, markdown=markdown, media=media,
                is_rtl=is_rtl, skip_entity_detection=skip_entity_detection,
            )

    class ReplyParameters(_Obj):
        def __init__(self, message_id=None, ephemeral_message_id=None, **kwargs):
            super().__init__(message_id=message_id, ephemeral_message_id=ephemeral_message_id, **kwargs)

    class EphemeralMessageParameters(_Obj):
        def __init__(self, receiver_user_id=None, callback_query_id=None,
                     replace_callback_query_message=None):
            super().__init__(
                receiver_user_id=receiver_user_id,
                callback_query_id=callback_query_id,
                replace_callback_query_message=replace_callback_query_message,
            )

    class Client:
        def __init__(self, name=None, **kwargs):
            self.name = name
            self.kwargs = kwargs
            self.handlers = []

        async def send_rich_message(self, **kwargs):
            raise NotImplementedError

        def _decorator(self, kind, flt):
            def register(func):
                self.handlers.append((kind, flt, func))
                return func
            return register

        def on_message(self, flt=None):
            return self._decorator("message", flt)

        def on_callback_query(self, flt=None):
            return self._decorator("callback_query", flt)

    class _Filters:
        @staticmethod
        def command(name):
            return ("command", name)

        @staticmethod
        def regex(pattern):
            return ("regex", pattern)

    enums.ParseMode = ParseMode
    errors.MessageNotModified = MessageNotModified
    pytypes.InputRichMessage = InputRichMessage
    pytypes.ReplyParameters = ReplyParameters
    pytypes.EphemeralMessageParameters = EphemeralMessageParameters
    pyrogram.Client = Client
    pyrogram.filters = _Filters()
    pyrogram.enums = enums
    pyrogram.errors = errors
    pyrogram.types = pytypes
    pyrogram.__stub__ = True

    sys.modules["pyrogram"] = pyrogram
    sys.modules["pyrogram.enums"] = enums
    sys.modules["pyrogram.errors"] = errors
    sys.modules["pyrogram.types"] = pytypes
    return True
