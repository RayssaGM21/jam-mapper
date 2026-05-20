"""Performance analysis page."""

import pandas as pd
import streamlit as st

from jam_mapper.web.components.charts import render_bar_list
from jam_mapper.web.components.lists import render_rank_list, render_summary_grid
from jam_mapper.web.components.layout import render_header


def _plot(data: pd.DataFrame, x: str, y: str, color: str = "#2563eb"):
    render_bar_list(data, y, x, color)


def render(df: pd.DataFrame):
    render_header("Performance", "Gargalos tecnicos, tempo e complexidade")

    if df.empty:
        st.warning("Nenhum dado disponivel. Execute a sincronizacao.")
        return

    tabs = st.tabs(["Temas", "Tempo", "Complexidade", "Correcao", "Tabela"])
    status_label_col = "effectiveStatusLabel" if "effectiveStatusLabel" in df.columns else "statusLabel"
    done_col = "effective_is_done" if "effective_is_done" in df.columns else "is_done"
    time_col = "effectiveTimeSpentMinutes" if "effectiveTimeSpentMinutes" in df.columns else "timeSpentMinutes"

    with tabs[0]:
        st.markdown("<div class='card'><h2 class='section-title'>Temas que mais pedem atencao</h2>", unsafe_allow_html=True)
        exploded = df.explode("tags_list").dropna(subset=["tags_list"])
        if not exploded.empty:
            grouped = (
                exploded.groupby("tags_list")
                .agg(
                    dificuldade_pessoal=("personalDifficulty", "mean"),
                    tempo_total=("timeSpentMinutes", "sum"),
                    pendentes=(done_col, lambda s: int((~s).sum())),
                    quantidade=("challengeId", "count"),
                )
                .reset_index()
            )
            grouped["score"] = grouped["dificuldade_pessoal"] * 8 + grouped["tempo_total"] / 30 + grouped["pendentes"]
            _plot(grouped.sort_values("score", ascending=False).head(15).sort_values("score"), "score", "tags_list", "#dc2626")
        else:
            st.info("Sem tags disponiveis.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='card'><h2 class='section-title'>Mais tempo gasto por voce</h2>", unsafe_allow_html=True)
            top = df.sort_values(time_col, ascending=False).head(15)
            render_rank_list(
                {
                    "title": row.get("title") or row.get("challengeId"),
                    "meta": f"{row.get(status_label_col)} | {int(row.get('attempts') or row.get('attemptsFromReports') or 0)} tentativas | dificuldade {int(row.get('personalDifficulty') or 0)}",
                    "value": int(row.get(time_col) or 0),
                }
                for _, row in top.head(10).iterrows()
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("<div class='card'><h2 class='section-title'>Mais lentos no catalogo AWS</h2>", unsafe_allow_html=True)
            top_global = df.sort_values("avgSolveSeconds", ascending=False).head(15)
            render_rank_list(
                {
                    "title": row.get("title") or row.get("challengeId"),
                    "meta": f"Nivel {int(row.get('difficulty') or 0)} | {int(row.get('numTasks') or 0)} tasks | {int(row.get('numInputTasks') or 0)} inputs",
                    "value": f"{int(row.get('avgSolveSeconds') or 0)}s",
                }
                for _, row in top_global.head(10).iterrows()
            )
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown("<div class='card'><h2 class='section-title'>Complexidade operacional</h2>", unsafe_allow_html=True)
        complex_df = df.copy()
        complex_df["complexidade"] = (
            complex_df["difficulty"].fillna(0) * 10
            + complex_df["numInputTasks"].fillna(0) * 4
            + complex_df["numTasks"].fillna(0) * 2
        )
        _plot(
            complex_df.sort_values("complexidade", ascending=False).head(20).sort_values("complexidade"),
            "complexidade",
            "title",
            "#d97706",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown("<div class='card'><h2 class='section-title'>Desafios por mecanismo de correcao</h2>", unsafe_allow_html=True)
        rows = [
            {"Tipo": "Campo de resposta", "Quantidade": int((df["hasInputAnswer"] | (df["numInputTasks"] > 0)).sum())},
            {"Tipo": "Lambda", "Quantidade": int((df["hasLambdaValidation"] | (df["numLambdaTasks"] > 0)).sum())},
            {"Tipo": "IA", "Quantidade": int((df["hasAiValidation"] | (df["numAiTasks"] > 0)).sum())},
            {"Tipo": "Sem tasks detalhadas", "Quantidade": int(df["numTasks"].eq(0).sum())},
        ]
        render_summary_grid({"label": row["Tipo"], "value": row["Quantidade"]} for row in rows)

        input_df = df[df["hasInputAnswer"] | (df["numInputTasks"] > 0)]
        st.markdown("<h3 class='section-title'>Com campo de resposta</h3>", unsafe_allow_html=True)
        st.dataframe(
            input_df[["title", "category", "difficulty", "numInputTasks", "avgSolveSeconds", "passRate"]].rename(
                columns={
                    "title": "Desafio",
                    "category": "Categoria",
                    "difficulty": "Nivel",
                    "numInputTasks": "Tasks com input",
                    "avgSolveSeconds": "Media global (s)",
                    "passRate": "Pass rate",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        cols = [
            "challengeId",
            "title",
            status_label_col,
            "difficulty",
            "personalDifficulty",
            "numInputTasks",
            "numLambdaTasks",
            "numAiTasks",
            time_col,
            "attempts",
            "numTasks",
            "avgSolveSeconds",
            "passRate",
        ]
        st.dataframe(
            df[cols].rename(
                columns={
                    "challengeId": "ID",
                    "title": "Desafio",
                    "statusLabel": "Status",
                    "effectiveStatusLabel": "Status",
                    "difficulty": "Nivel AWS",
                    "personalDifficulty": "Dificuldade pessoal",
                    "numInputTasks": "Input",
                    "numLambdaTasks": "Lambda",
                    "numAiTasks": "IA",
                    "timeSpentMinutes": "Minutos",
                    "effectiveTimeSpentMinutes": "Minutos",
                    "attempts": "Tentativas",
                    "numTasks": "Tasks",
                    "avgSolveSeconds": "Media global (s)",
                    "passRate": "Pass rate",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
