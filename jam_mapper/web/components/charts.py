"""Chart helpers rendered without Vega-Lite dependencies."""

from html import escape

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def render_bar_list(data: pd.DataFrame, label_col: str, value_col: str, color: str = "#2563eb"):
    if data.empty:
        st.info("Sem dados suficientes.")
        return

    chart = data[[label_col, value_col]].copy()
    chart[value_col] = pd.to_numeric(chart[value_col], errors="coerce").fillna(0)
    max_value = float(chart[value_col].max() or 1)

    rows = []
    for _, row in chart.iterrows():
        value = float(row[value_col] or 0)
        width = max(2, min(100, (value / max_value) * 100))
        rows.append(
            "<div class='bar-row'>"
            f"<div class='bar-label' title='{escape(str(row[label_col]))}'>{escape(str(row[label_col]))}</div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{width:.1f}%;background:{color}'></div></div>"
            f"<div class='bar-value'>{value:.1f}</div>"
            "</div>"
        )
    html = f"""
    <style>
      body {{ margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
      .bar-list {{ display: flex; flex-direction: column; gap: 10px; }}
      .bar-row {{ display: grid; grid-template-columns: minmax(130px, 240px) 1fr auto; gap: 12px; align-items: center; }}
      .bar-label {{ color: #111827; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
      .bar-track {{ height: 10px; border-radius: 999px; background: #e8eef6; overflow: hidden; }}
      .bar-fill {{ height: 100%; border-radius: 999px; }}
      .bar-value {{ color: #667085; font-size: 12px; min-width: 52px; text-align: right; }}
    </style>
    <div class='bar-list'>{''.join(rows)}</div>
    """
    components.html(html, height=max(90, len(rows) * 24 + 12), scrolling=False)


def render_tag_performance(df: pd.DataFrame, top_n: int = 30):
    if df.empty:
        st.info("Nenhum dado disponivel para graficos")
        return

    exploded = df.explode("tags_list").dropna(subset=["tags_list"])
    if exploded.empty:
        st.info("Sem dados de tags disponiveis.")
        return

    grouped = (
        exploded.groupby("tags_list")["avgSolveSeconds"]
        .mean()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )
    render_bar_list(grouped.sort_values("avgSolveSeconds"), "tags_list", "avgSolveSeconds")
