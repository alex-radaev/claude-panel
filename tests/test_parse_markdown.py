import pytest

from claude_panel.server import _parse_markdown_to_sections


@pytest.mark.parametrize("text,expected", [
    pytest.param(
        "## Summary\nHello world",
        [{"id": "summary", "title": "Summary", "content": "Hello world"}],
        id="single-section",
    ),
    pytest.param(
        "## First\nAAA\n## Second\nBBB",
        [
            {"id": "first", "title": "First", "content": "AAA"},
            {"id": "second", "title": "Second", "content": "BBB"},
        ],
        id="two-sections",
    ),
    pytest.param(
        "",
        [],
        id="empty-input",
    ),
    pytest.param(
        "Just some text\nno headings",
        [{"id": "content", "title": "Content", "content": "Just some text\nno headings"}],
        id="no-headings-becomes-content",
    ),
    pytest.param(
        "Preamble here\n## After",
        [
            {"id": "intro", "title": "Overview", "content": "Preamble here"},
            {"id": "after", "title": "After", "content": ""},
        ],
        id="preamble-before-heading",
    ),
    pytest.param(
        "## Empty Section",
        [{"id": "empty-section", "title": "Empty Section", "content": ""}],
        id="heading-with-no-body",
    ),
])
def test_parse_markdown_to_sections(text, expected):
    result = _parse_markdown_to_sections(text)
    assert result == expected


def test_section_id_strips_special_chars():
    result = _parse_markdown_to_sections("## What's Next?!\nstuff")
    assert result[0]["id"] == "whats-next"
    assert result[0]["title"] == "What's Next?!"


def test_multiline_content_preserved():
    text = "## Notes\nline 1\nline 2\nline 3"
    result = _parse_markdown_to_sections(text)
    assert result[0]["content"] == "line 1\nline 2\nline 3"


def test_trailing_whitespace_stripped():
    text = "## Padded\n  content  \n\n"
    result = _parse_markdown_to_sections(text)
    assert result[0]["content"] == "content"
