import pytest

from claude_panel.curator import (
    ensure_multi,
    ensure_screen_order,
    update_main,
    update_mood,
    update_status_section,
    set_active,
)


# ── ensure_multi ──


def test_ensure_multi_from_empty_state():
    result = ensure_multi({})
    assert result["mode"] == "multi"
    assert result["screens"] == {}
    assert result["screen_order"] == []
    assert result["active"] is None


def test_ensure_multi_preserves_existing_multi():
    state = {"mode": "multi", "screens": {"main": {}}, "screen_order": ["main"], "active": "main"}
    result = ensure_multi(state)
    assert result is state


# ── ensure_screen_order ──


@pytest.mark.parametrize("order,expected", [
    pytest.param(
        ["status", "main", "ambient"],
        ["main", "status", "ambient"],
        id="reorders-standard",
    ),
    pytest.param(
        ["custom", "main"],
        ["main", "custom"],
        id="standard-before-custom",
    ),
    pytest.param(
        ["ambient", "custom1", "status", "custom2", "main"],
        ["main", "status", "ambient", "custom1", "custom2"],
        id="complex-mix",
    ),
    pytest.param([], [], id="empty-list"),
    pytest.param(["custom_only"], ["custom_only"], id="no-standard-screens"),
])
def test_ensure_screen_order(order, expected):
    assert ensure_screen_order(order) == expected


# ── update_main ──


def test_update_main_creates_screen_and_sets_active():
    sections = [{"id": "test", "title": "Test", "content": "hello"}]
    result = update_main({}, sections)

    assert result["screens"]["main"]["type"] == "sections"
    assert result["screens"]["main"]["sections"] == sections
    assert result["active"] == "main"
    assert "main" in result["screen_order"]


def test_update_main_replaces_existing_sections():
    state = update_main({}, [{"id": "old", "title": "Old", "content": "old"}])
    new_sections = [{"id": "new", "title": "New", "content": "new"}]
    result = update_main(state, new_sections)

    assert result["screens"]["main"]["sections"] == new_sections


# ── update_status_section ──


def test_update_status_section_creates_defaults_and_updates():
    result = update_status_section({}, "objective", "Build the thing")

    status = result["screens"]["status"]
    assert status["type"] == "sections"
    objective = next(s for s in status["sections"] if s["id"] == "objective")
    assert objective["content"] == "Build the thing"


def test_update_status_section_upserts_existing():
    state = update_status_section({}, "objective", "v1")
    result = update_status_section(state, "objective", "v2")

    sections = result["screens"]["status"]["sections"]
    objectives = [s for s in sections if s["id"] == "objective"]
    assert len(objectives) == 1
    assert objectives[0]["content"] == "v2"


def test_update_status_section_appends_unknown_id():
    state = update_status_section({}, "objective", "test")
    result = update_status_section(state, "custom_metric", "42")

    sections = result["screens"]["status"]["sections"]
    custom = next(s for s in sections if s["id"] == "custom_metric")
    assert custom["content"] == "42"
    assert custom["title"] == "Custom Metric"


def test_update_status_section_adds_status_to_screen_order():
    result = update_status_section({}, "objective", "x")
    assert "status" in result["screen_order"]


# ── update_mood ──


def test_update_mood_sets_main_to_mood_type():
    result = update_mood({}, "🔥", "shipping fast", "almost there")

    main = result["screens"]["main"]
    assert main["type"] == "mood"
    assert main["emoji"] == "🔥"
    assert main["context"] == "shipping fast"
    assert "CONTEXT = 'shipping fast'" in main["code"]
    assert "TIP = 'almost there'" in main["code"]
    assert result["active"] == "main"


def test_update_mood_without_tip():
    result = update_mood({}, "☕", "coffee break")
    assert "TIP = ''" in result["screens"]["main"]["code"]


# ── set_active ──


def test_set_active_switches_screen():
    state = {"screens": {"main": {}, "status": {}}, "active": "main"}
    result = set_active(state, "status")
    assert result["active"] == "status"


def test_set_active_ignores_nonexistent_screen():
    state = {"screens": {"main": {}}, "active": "main"}
    result = set_active(state, "nonexistent")
    assert result["active"] == "main"
