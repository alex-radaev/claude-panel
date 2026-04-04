import pytest

from claude_panel.session import get_session_id_from_transcript, session_state_dir, session_state_file


@pytest.mark.parametrize("path,expected", [
    pytest.param(
        "/home/user/.claude/sessions/a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4.jsonl",
        "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        id="valid-uuid-stem",
    ),
    pytest.param(
        "/tmp/abcdef01-2345-6789-abcd-ef0123456789.jsonl",
        "abcdef01-2345-6789-abcd-ef0123456789",
        id="uuid-with-dashes",
    ),
    pytest.param("short.jsonl", None, id="stem-too-short"),
    pytest.param("session.json", None, id="wrong-extension"),
    pytest.param("", None, id="empty-string"),
    pytest.param(None, None, id="none-input"),
])
def test_get_session_id_from_transcript(path, expected):
    assert get_session_id_from_transcript(path) == expected


def test_session_state_file_contains_state_json():
    result = session_state_file("test-session-123")
    assert result.name == "state.json"
    assert "test-session-123" in str(result)


def test_session_state_dir_uses_session_id():
    result = session_state_dir("my-session")
    assert result.name == "my-session"
