"""Reusable card components (wraps theme utilities)."""
from typing import List
from jam_mapper.web import theme


def render_kpi_card(number: str, label: str, color: str = "text", help_text: str = "") -> str:
    return theme.render_kpi_card(number, label, color, help_text)


def render_challenge_card(
    title: str,
    tags: List[str],
    difficulty: int,
    avg_time: int,
    services: List[str] = None,
    status: str = "not_started",
    personal_difficulty: int = 0,
    time_spent: int = 0,
) -> str:
    return theme.render_challenge_card(
        title,
        tags,
        difficulty,
        avg_time,
        services,
        status,
        personal_difficulty,
        time_spent,
    )
