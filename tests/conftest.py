import pytest

from tests import pyrogram_stub

pyrogram_stub.install_if_missing()

_LAYERS = ("unit", "guards", "integrations")
_MARKERS = {"unit": "unit", "guards": "guard", "integrations": "integration"}


def pytest_collection_modifyitems(config, items):
    for item in items:
        parts = item.path.parts
        for layer in _LAYERS:
            if layer in parts:
                item.add_marker(getattr(pytest.mark, _MARKERS[layer]))
                break
        else:
            raise pytest.UsageError(
                f"{item.nodeid} is not inside tests/unit, tests/guards or tests/integrations"
            )
