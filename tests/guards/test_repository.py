import io
import pathlib
import tokenize

import richgram
from richgram import rich_ui

ROOT = pathlib.Path(__file__).resolve().parents[2]


def python_files():
    files = [ROOT / "bot.py"]
    for folder in ("richgram", "tests"):
        files += sorted((ROOT / folder).rglob("*.py"))
    return files


def test_no_comments_in_python_files():
    offenders = []
    for path in python_files():
        source = path.read_text(encoding="utf-8")
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                offenders.append(f"{path.relative_to(ROOT)}:{token.start[0]}")
    assert not offenders, "comment lines found: " + ", ".join(offenders)


def test_every_exported_name_exists():
    for name in richgram.__all__:
        assert hasattr(richgram, name), name
    for name in rich_ui.__all__:
        assert hasattr(rich_ui, name), name


def test_all_has_no_duplicates():
    assert len(rich_ui.__all__) == len(set(rich_ui.__all__))
    assert len(richgram.__all__) == len(set(richgram.__all__))


def test_public_helpers_are_documented_in_the_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = [name for name in rich_ui.__all__ if name != "RICH_AVAILABLE" and name not in readme]
    assert not missing, "missing from README: " + ", ".join(missing)


def test_version_matches_pyproject_dynamic_attr():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'attr = "richgram.__version__"' in pyproject
    assert richgram.__version__


def test_kurigram_is_credited_with_the_right_link():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "https://github.com/kurigram-org/kurigram" in readme
    assert "KurimuzonAkuma/kurigram" not in readme
  
