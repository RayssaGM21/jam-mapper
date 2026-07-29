"""Training plan view."""

import pandas as pd
import streamlit as st

from jam_mapper.web.components.layout import render_header
from jam_mapper.web.context import recommend_challenges


def filter_training_candidates(df: pd.DataFrame, category: list[str] | None, status_filter: str | None, status_col: str) -> pd.DataFrame:
    """Filter training candidates by category and a simple status bucket."""
    filtered = df.copy()

    if category:
        selected_categories = [value for value in category if value]
        if selected_categories:
            filtered = filtered[filtered["category"].fillna("").astype(str).isin(selected_categories)]

    if status_filter and status_filter != "Todos":
        if status_filter == "Concluidos":
            filtered = filtered[filtered[status_col].eq("done")]
        elif status_filter == "Revisao":
            filtered = filtered[filtered[status_col].eq("review")]
        elif status_filter == "Nao iniciados":
            filtered = filtered[filtered[status_col].eq("not_started")]
        elif status_filter == "Em andamento":
            filtered = filtered[filtered[status_col].isin(["in_progress", "done", "review"])]

    return filtered


def render(df: pd.DataFrame):
    render_header("Treino", "Monte blocos de estudo objetivos para a semana")

    if df.empty:
        st.warning("Nenhum dado disponivel para treinar. Execute a sincronizacao.")
        return

    st.markdown("<div class='card'><h2 class='section-title'>Plano de treino</h2>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    hours = c1.number_input("Horas disponiveis na semana", min_value=1, max_value=80, value=10)
    target_count = c2.number_input("Quantidade de jams", min_value=1, max_value=100, value=8)
    mode = c3.selectbox(
        "Estrategia",
        ["Prioridade", "Revisao", "Nao iniciados", "Mais dificeis", "Com input", "Lambda", "IA", "Com resolucao", "Sem resolucao"],
    )
    category_options = sorted({str(value).strip() for value in df["category"].dropna().astype(str).tolist() if str(value).strip()})
    selected_categories = c4.multiselect("Categoria", category_options, default=[])
    status_filter = c5.selectbox("Status", ["Todos", "Concluidos", "Revisao", "Nao iniciados", "Em andamento"])
    resolution_filter = c6.selectbox("Resolucao", ["Todos", "Com resolucao", "Sem resolucao"])

    plan = df.copy()
    status_col = "effectiveStatus" if "effectiveStatus" in plan.columns else "status"
    plan = filter_training_candidates(plan, selected_categories or None, status_filter, status_col)
    has_solution = plan.get("hasSolutionResolution", pd.Series(False, index=plan.index)).fillna(False).astype(bool)
    if "hasSolutionResolution" in plan.columns and resolution_filter != "Todos":
        has_resolution = resolution_filter == "Com resolucao"
        plan = plan[has_solution.eq(has_resolution)]
        has_solution = plan.get("hasSolutionResolution", pd.Series(False, index=plan.index)).fillna(False).astype(bool)
    if mode == "Prioridade":
        plan = recommend_challenges(plan, int(target_count))
    elif mode == "Revisao":
        plan = plan[plan[status_col].eq("review")].head(int(target_count))
    elif mode == "Nao iniciados":
        plan = plan[plan[status_col].eq("not_started")].sort_values(["difficulty", "avgSolveSeconds"], ascending=False).head(int(target_count))
    else:
        if mode == "Mais dificeis":
            plan = plan.sort_values(["personalDifficulty", "difficulty", "numInputTasks"], ascending=False).head(int(target_count))
        elif mode == "Com input":
            plan = plan[plan["hasInputAnswer"] | (plan["numInputTasks"] > 0)].sort_values(["difficulty", "avgSolveSeconds"], ascending=False).head(int(target_count))
        elif mode == "Lambda":
            plan = plan[plan["hasLambdaValidation"] | (plan["numLambdaTasks"] > 0)].sort_values(["difficulty", "avgSolveSeconds"], ascending=False).head(int(target_count))
        elif mode == "IA":
            plan = plan[plan["hasAiValidation"] | (plan["numAiTasks"] > 0)].sort_values(["difficulty", "avgSolveSeconds"], ascending=False).head(int(target_count))
        elif mode == "Com resolucao":
            plan = plan[has_solution].sort_values(["difficulty", "avgSolveSeconds"], ascending=False).head(int(target_count))
        else:
            plan = plan[~has_solution].sort_values(["difficulty", "avgSolveSeconds"], ascending=False).head(int(target_count))

    available_minutes = int(hours * 60)
    estimated_minutes = int(plan["avgSolveSeconds"].fillna(0).sum() / 60)
    st.progress(
        min(1.0, estimated_minutes / available_minutes) if available_minutes else 0,
        text=f"Estimativa global: {estimated_minutes}min de {available_minutes}min disponiveis",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h2 class='section-title'>Lista recomendada</h2>", unsafe_allow_html=True)
    if plan.empty:
        st.info("Nao ha desafios para essa estrategia.")
    else:
        table = plan[
            [
                "title",
                "effectiveStatusLabel" if "effectiveStatusLabel" in plan.columns else "statusLabel",
                "difficulty",
                "personalDifficulty",
                "timeSpentMinutes",
                "attempts",
                "solutionStatusLabel",
                "solutionReference",
                "numInputTasks",
                "numLambdaTasks",
                "numAiTasks",
                "avgSolveSeconds",
            ]
        ].rename(
            columns={
                "title": "Desafio",
                "statusLabel": "Status",
                "effectiveStatusLabel": "Status",
                "difficulty": "Nivel AWS",
                "personalDifficulty": "Dificuldade pessoal",
                "timeSpentMinutes": "Minutos ja gastos",
                "attempts": "Tentativas",
                "solutionStatusLabel": "Resolucao",
                "solutionReference": "Referencia",
                "numInputTasks": "Inputs",
                "numLambdaTasks": "Lambda",
                "numAiTasks": "IA",
                "avgSolveSeconds": "Media global (s)",
            }
        )
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.download_button(
            "Exportar plano CSV",
            table.to_csv(index=False),
            file_name="plano_treino_aws_jam.csv",
            use_container_width=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
