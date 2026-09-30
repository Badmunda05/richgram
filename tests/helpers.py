from contextlib import contextmanager
from types import SimpleNamespace

from richgram import rich_ui


@contextmanager
def patched(obj, name, value):
    original = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, original)


@contextmanager
def rich_available(value=True):
    with patched(rich_ui, "RICH_AVAILABLE", value):
        yield


class FakeClient:
    def __init__(self, fail=(), not_modified=()):
        self.calls = []
        self.fail = set(fail)
        self.not_modified = set(not_modified)
        self.bot_token = None

    def _record(self, name, kwargs):
        self.calls.append((name, kwargs))
        if name in self.not_modified:
            from pyrogram.errors import MessageNotModified
            raise MessageNotModified()
        if name in self.fail:
            raise RuntimeError(f"{name} failed")
        return SimpleNamespace(id=len(self.calls), call=name)

    def __getattr__(self, name):
        if name.startswith("_") or name in ("kwargs", "handlers"):
            raise AttributeError(name)
        if name in (
            "send_rich_message", "send_message", "edit_message_text", "edit_inline_text",
            "send_rich_message_draft", "edit_ephemeral_message_text", "delete_ephemeral_message",
        ):
            async def method(**kwargs):
                return self._record(name, kwargs)
            return method
        raise AttributeError(name)

    def names(self):
        return [name for name, _ in self.calls]

    def last(self, name=None):
        for call_name, kwargs in reversed(self.calls):
            if name is None or call_name == name:
                return kwargs
        return None


class FakeMessage:
    def __init__(self, client=None, chat_id=100, chat_type="private", message_id=7,
                 user_id=42, ephemeral_message_id=None):
        self._client = client or FakeClient()
        self.id = message_id
        self.chat = SimpleNamespace(id=chat_id, type=SimpleNamespace(value=chat_type))
        self.from_user = SimpleNamespace(id=user_id)
        self.message_thread_id = None
        self.ephemeral_message_id = ephemeral_message_id
        self.receiver_user = None
        self.deleted = False

    async def delete(self):
        self.deleted = True
        return True


class FakeCallbackQuery:
    def __init__(self, data="x", client=None, chat_type="private", inline_message_id=None):
        self._client = client or FakeClient()
        self.data = data
        self.id = "cbq-1"
        self.from_user = SimpleNamespace(id=42)
        self.inline_message_id = inline_message_id
        self.message = None if inline_message_id else FakeMessage(
            self._client, chat_type=chat_type
        )
        self.answers = []

    async def answer(self, text=None, show_alert=None, **kwargs):
        self.answers.append((text, show_alert))
        return True
