
import pytest

from app.code_search import CodeSearch


@pytest.fixture
def repo(tmp_path):
    """Create a tiny fake repository for testing."""
    (tmp_path / "auth.py").write_text(
        "def login():\n    return 'authenticated'\n",
        encoding="utf-8",
    )

    (tmp_path / "database.py").write_text(
        "def connect():\n    pass\n",
        encoding="utf-8",
    )

    return CodeSearch(str(tmp_path))


def test_search_files(repo):
    results = repo.search_files("auth")

    assert len(results) == 1
    assert results[0]["path"] == "auth.py"


def test_search_code_returns_line_numbers(repo):
    results = repo.search_code("authenticated")

    assert len(results) == 1
    assert results[0]["path"] == "auth.py"
    assert results[0]["line"] == 2


def test_read_file_includes_line_numbers(repo):
    result = repo.read_file("auth.py", 1, 2)

    assert "1: def login():" in result["content"]
    assert "2:     return 'authenticated'" in result["content"]


def test_reject_path_traversal(repo):
    with pytest.raises(ValueError):
        repo.read_file("../outside.txt")


def test_reject_empty_search(repo):
    with pytest.raises(ValueError):
        repo.search_code("   ")
