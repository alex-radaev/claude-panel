import json
from unittest import mock

import pytest

from claude_panel import reviews


def _make_pr(url: str, title: str = "Test PR", author: str = "dev") -> dict:
    return {
        "url": url,
        "title": title,
        "author": {"login": author},
        "repository": {"nameWithOwner": "org/repo"},
        "createdAt": "2026-01-01T00:00:00Z",
    }


# ── _format_pr_line ──


def test_format_pr_line_includes_all_fields():
    pr = _make_pr("https://github.com/org/repo/pull/1", title="Fix bug", author="alice")
    line = reviews._format_pr_line(pr)

    assert "Fix bug" in line
    assert "org/repo" in line
    assert "@alice" in line
    assert "https://github.com/org/repo/pull/1" in line


def test_format_pr_line_handles_missing_fields():
    line = reviews._format_pr_line({"title": "Solo"})
    assert "Solo" in line


# ── _build_status_section ──


def test_build_status_section_returns_none_for_empty():
    assert reviews._build_status_section([]) is None


def test_build_status_section_returns_section_with_count():
    prs = [_make_pr(f"https://url/{i}") for i in range(3)]
    result = reviews._build_status_section(prs)

    assert result["id"] == "reviews"
    assert "3" in result["title"]
    assert result["content"].count("- ") == 3


# ── _time_ago ──


def test_time_ago_returns_empty_for_invalid():
    assert reviews._time_ago("not-a-date") == ""


@mock.patch("claude_panel.reviews.datetime")
def test_time_ago_minutes(mock_dt):
    from datetime import datetime, timezone, timedelta
    now = datetime(2026, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
    mock_dt.now.return_value = now
    mock_dt.fromisoformat = datetime.fromisoformat
    result = reviews._time_ago("2026-01-01T12:10:00+00:00")
    assert result == "20m ago"


@mock.patch("claude_panel.reviews.datetime")
def test_time_ago_hours(mock_dt):
    from datetime import datetime, timezone
    now = datetime(2026, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
    mock_dt.now.return_value = now
    mock_dt.fromisoformat = datetime.fromisoformat
    result = reviews._time_ago("2026-01-01T12:00:00+00:00")
    assert result == "3h ago"


@mock.patch("claude_panel.reviews.datetime")
def test_time_ago_days(mock_dt):
    from datetime import datetime, timezone
    now = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    mock_dt.now.return_value = now
    mock_dt.fromisoformat = datetime.fromisoformat
    result = reviews._time_ago("2026-01-01T12:00:00+00:00")
    assert result == "4d ago"


# ── find_unseen_reviews ──


def test_find_unseen_first_run_seeds_baseline(tmp_path):
    baseline = tmp_path / "baseline.json"
    notified = tmp_path / "notified.json"

    with mock.patch.object(reviews, "BASELINE_FILE", baseline), \
         mock.patch.object(reviews, "NOTIFIED_FILE", notified), \
         mock.patch.object(reviews, "REVIEWS_DIR", tmp_path):
        prs = [_make_pr("https://pr/1"), _make_pr("https://pr/2")]
        result = reviews.find_unseen_reviews(prs)

    assert result == []
    assert set(json.loads(baseline.read_text())) == {"https://pr/1", "https://pr/2"}


def test_find_unseen_returns_new_prs(tmp_path):
    baseline = tmp_path / "baseline.json"
    notified = tmp_path / "notified.json"
    baseline.write_text(json.dumps(["https://pr/1"]))
    notified.write_text(json.dumps(["https://pr/1"]))

    with mock.patch.object(reviews, "BASELINE_FILE", baseline), \
         mock.patch.object(reviews, "NOTIFIED_FILE", notified), \
         mock.patch.object(reviews, "REVIEWS_DIR", tmp_path):
        prs = [_make_pr("https://pr/1"), _make_pr("https://pr/2", title="New one")]
        result = reviews.find_unseen_reviews(prs)

    assert len(result) == 1
    assert result[0]["title"] == "New one"


def test_find_unseen_does_not_re_notify(tmp_path):
    baseline = tmp_path / "baseline.json"
    notified = tmp_path / "notified.json"
    baseline.write_text(json.dumps(["https://pr/1"]))
    notified.write_text(json.dumps(["https://pr/1", "https://pr/2"]))

    with mock.patch.object(reviews, "BASELINE_FILE", baseline), \
         mock.patch.object(reviews, "NOTIFIED_FILE", notified), \
         mock.patch.object(reviews, "REVIEWS_DIR", tmp_path):
        prs = [_make_pr("https://pr/1"), _make_pr("https://pr/2")]
        result = reviews.find_unseen_reviews(prs)

    assert result == []
