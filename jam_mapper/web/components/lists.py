"""Readable list/summary components for Streamlit pages."""

from html import escape
from typing import Iterable, Mapping

import streamlit as st


def render_summary_grid(items: Iterable[Mapping[str, object]]):
    cells = []
    for item in items:
        value = escape(str(item.get("value", "")))
        label = escape(str(item.get("label", "")))
        cells.append(
            "<div class='summary-item'>"
            f"<div class='summary-value'>{value}</div>"
            f"<div class='summary-label'>{label}</div>"
            "</div>"
        )
    st.markdown(f"<div class='summary-grid'>{''.join(cells)}</div>", unsafe_allow_html=True)


def render_rank_list(items: Iterable[Mapping[str, object]], value_suffix: str = ""):
    rows = []
    for idx, item in enumerate(items, start=1):
        title = escape(str(item.get("title", "")))
        meta = escape(str(item.get("meta", "")))
        value = escape(str(item.get("value", "")))
        suffix = escape(value_suffix)
        rows.append(
            "<div class='rank-item'>"
            f"<div class='rank-number'>{idx}</div>"
            "<div>"
            f"<div class='rank-title' title='{title}'>{title}</div>"
            f"<div class='rank-meta'>{meta}</div>"
            "</div>"
            f"<div class='rank-value'>{value}{suffix}</div>"
            "</div>"
        )
    if not rows:
        st.info("Sem dados para exibir.")
        return
    st.markdown(f"<div class='rank-list'>{''.join(rows)}</div>", unsafe_allow_html=True)
