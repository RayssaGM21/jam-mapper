"""Dashboard page."""

import pandas as pd
import streamlit as st

from jam_mapper.web.components.cards import render_kpi_card
from jam_mapper.web.components.charts import render_bar_list
from jam_mapper.web.components.lists import render_rank_list, render_summary_grid
from jam_mapper.web.components.layout import render_header
from jam_mapper.web.context import format_duration, recommend_challenges


def _safe_int(value, default: int = 0) -> int:
    if pd.isna(value):
        return default
    return int(value)


def _bar_chart(data: pd.DataFrame, x: str, y: str, title: str):
    render_bar_list(data, y, x)


def render(df: pd.DataFrame):
    render_header("AWS Jam Performance Hub", "Dashboard de treino, catalogo e preparo para WorldSkills")

    total = len(df)
    status_col = "effectiveStatus" if "effectiveStatus" in df.columns else "status"
    time_col = "effectiveTimeSpentMinutes" if "effectiveTimeSpentMinutes" in df.columns else "timeSpentMinutes"
    done = int(df[status_col].eq("done").sum())
    review = int(df[status_col].eq("review").sum())
    in_progress = int(df[status_col].eq("in_progress").sum())
    remaining = total - done
    completion = round((done / total) * 100, 1) if total else 0
    total_minutes = _safe_int(df[time_col].sum())
    practiced_minutes = df.loc[df[time_col] > 0, time_col]
    avg_personal = _safe_int(practiced_minutes.mean()) if not practiced_minutes.empty else 0
    input_count = int((df["hasInputAnswer"] | (df["numInputTasks"].fillna(0) > 0)).sum())
    lambda_count = int((df["hasLambdaValidation"] | (df["numLambdaTasks"].fillna(0) > 0)).sum())
    ai_count = int((df["hasAiValidation"] | (df["numAiTasks"].fillna(0) > 0)).sum())

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(render_kpi_card(total, "Jams catalogados"), unsafe_allow_html=True)
    k2.markdown(render_kpi_card(f"{completion}%", "Progresso concluido", "success", f"{done} concluidos"), unsafe_allow_html=True)
    k3.markdown(render_kpi_card(remaining, "Ainda faltam", "warning"), unsafe_allow_html=True)
    k4.markdown(render_kpi_card(format_duration(total_minutes), "Tempo treinado", "accent"), unsafe_allow_html=True)
    k5.markdown(render_kpi_card(review + in_progress, "Em foco", "danger", f"{review} revisar, {in_progress} em andamento"), unsafe_allow_html=True)

    st.progress(done / total if total else 0, text=f"{done} de {total} desafios concluidos")
    st.caption(
        f"Tempo medio nos desafios praticados: {format_duration(avg_personal)} | "
        f"{input_count} com campo de resposta | {lambda_count} com Lambda | {ai_count} com IA detectada"
    )

    if "eventsStarted" in df.columns:
        event_started = int(df["eventsStarted"].fillna(0).gt(0).sum())
        event_solved = int(df["eventsSolved"].fillna(0).gt(0).sum())
        event_clues = int(df["cluesFromReports"].fillna(0).sum())
        event_attempts = int(df["attemptsFromReports"].fillna(0).sum())
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Vistos em eventos", event_started)
        e2.metric("Resolvidos em eventos", event_solved)
        e3.metric("Dicas usadas", event_clues)
        e4.metric("Tentativas", event_attempts)

    left, right = st.columns([1.7, 1])
    with left:
        with st.container():
            st.markdown("<h2 class='section-title'>Mapa de dificuldade por tema</h2>", unsafe_allow_html=True)
            exploded = df.explode("tags_list").dropna(subset=["tags_list"])
            if exploded.empty:
                st.info("Sem tags no catalogo.")
            else:
                grouped = (
                    exploded.groupby("tags_list")
                    .agg(
                        media_pessoal=("personalDifficulty", "mean"),
                        tempo_medio=("timeSpentMinutes", "mean"),
                        quantidade=("challengeId", "count"),
                    )
                    .reset_index()
                )
                grouped["prioridade"] = grouped["media_pessoal"] * 10 + grouped["tempo_medio"]
                top = grouped.sort_values("prioridade", ascending=False).head(12)
                _bar_chart(top.sort_values("prioridade"), "prioridade", "tags_list", "Prioridade")

    with right:
        st.markdown("<div class='card'><h2 class='section-title'>Treinar agora</h2>", unsafe_allow_html=True)
        rec = recommend_challenges(df, 6)
        for _, row in rec.iterrows():
            st.markdown(
                f"""
                <div style='padding:10px 0;border-bottom:1px solid var(--border)'>
                    <div style='font-size:13px;font-weight:700'>{row.get('title') or 'Sem titulo'}</div>
                    <div class='muted' style='font-size:12px;margin-top:3px'>
                        {row.get('statusLabel')} | dificuldade {int(row.get('personalDifficulty') or 0)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='card'><h2 class='section-title'>Status do catalogo</h2>", unsafe_allow_html=True)
        label_col = "effectiveStatusLabel" if "effectiveStatusLabel" in df.columns else "statusLabel"
        status = df[label_col].value_counts().rename_axis("Status").reset_index(name="Quantidade")
        render_summary_grid(
            {"label": row["Status"], "value": int(row["Quantidade"])}
            for _, row in status.iterrows()
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card'><h2 class='section-title'>Ultimos registros</h2>", unsafe_allow_html=True)
        recent = df[df["updatedAt"].notna()] if "updatedAt" in df.columns else pd.DataFrame()
        if recent.empty:
            st.info("Atualize um desafio em Explorar para iniciar seu historico.")
        else:
            label_col = "effectiveStatusLabel" if "effectiveStatusLabel" in recent.columns else "statusLabel"
            time_col = "effectiveTimeSpentMinutes" if "effectiveTimeSpentMinutes" in recent.columns else "timeSpentMinutes"
            render_rank_list(
                {
                    "title": row.get("title") or row.get("challengeId"),
                    "meta": f"{row.get(label_col)} | {int(row.get(time_col) or 0)} min | {int(row.get('attempts') or 0)} tentativas",
                    "value": f"D{int(row.get('personalDifficulty') or 0)}",
                }
                for _, row in recent.sort_values("updatedAt", ascending=False).head(6).iterrows()
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h2 class='section-title'>Mapa por tipo de correcao</h2>", unsafe_allow_html=True)
    validation_rows = [
        {"Tipo": "Campo de resposta", "Challenges": input_count},
        {"Tipo": "Lambda", "Challenges": lambda_count},
        {"Tipo": "IA", "Challenges": ai_count},
        {"Tipo": "Sem detalhe de task", "Challenges": int(df["numTasks"].fillna(0).eq(0).sum())},
    ]
    render_summary_grid(
        {"label": row["Tipo"], "value": row["Challenges"]}
        for row in validation_rows
    )
    st.markdown("</div>", unsafe_allow_html=True)
