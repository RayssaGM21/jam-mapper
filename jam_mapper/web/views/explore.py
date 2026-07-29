"""Challenge exploration and personal tracking page."""

from datetime import date

import pandas as pd
import streamlit as st

from jam_mapper.core.db import Database
from jam_mapper.web.components.cards import render_challenge_card
from jam_mapper.web.components.layout import render_header
from jam_mapper.web.context import STATUS_LABELS


STATUS_BY_LABEL = {v: k for k, v in STATUS_LABELS.items()}


def _filter_df(df: pd.DataFrame) -> pd.DataFrame:
    st.markdown("<div class='card'><h2 class='section-title'>Filtros</h2>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1.4, 1, 1, 1])

    search = col1.text_input("Buscar", placeholder="Nome, tag ou servico")
    status = col2.selectbox("Status", ["Todos"] + list(STATUS_LABELS.values()))
    difficulties = sorted(int(x) for x in df["difficulty"].dropna().unique().tolist())
    difficulty = col3.selectbox("Nivel AWS", ["Todos"] + difficulties)
    focus = col4.selectbox(
        "Foco",
        ["Todos", "Com input", "Lambda", "IA", "Revisao", "Sem iniciar", "Com resolucao", "Sem resolucao", "Ja visto em evento"],
    )

    tag_list = sorted(set(sum(df["tags_list"].tolist(), [])))
    service_list = sorted(set(sum(df["services_list"].tolist(), [])))
    col5, col6 = st.columns(2)
    tag = col5.selectbox("Tag", ["Todos"] + tag_list)
    service = col6.selectbox("Servico AWS", ["Todos"] + service_list)
    st.markdown("</div>", unsafe_allow_html=True)

    q = df.copy()
    status_col = "effectiveStatus" if "effectiveStatus" in q.columns else "status"
    if search:
        text = search.lower()
        q = q[
            q["title"].fillna("").str.lower().str.contains(text)
            | q["tags_list"].apply(lambda values: any(text in str(v).lower() for v in values))
            | q["services_list"].apply(lambda values: any(text in str(v).lower() for v in values))
        ]
    if status != "Todos":
        q = q[q[status_col].eq(STATUS_BY_LABEL[status])]
    if difficulty != "Todos":
        q = q[q["difficulty"].eq(difficulty)]
    if tag != "Todos":
        q = q[q["tags_list"].apply(lambda values: tag in values)]
    if service != "Todos":
        q = q[q["services_list"].apply(lambda values: service in values)]
    if focus == "Com input":
        q = q[q["hasInputAnswer"] | (q["numInputTasks"].fillna(0) > 0)]
    elif focus == "Lambda":
        q = q[q["hasLambdaValidation"] | (q["numLambdaTasks"].fillna(0) > 0)]
    elif focus == "IA":
        q = q[q["hasAiValidation"] | (q["numAiTasks"].fillna(0) > 0)]
    elif focus == "Revisao":
        q = q[q[status_col].eq("review")]
    elif focus == "Sem iniciar":
        q = q[q[status_col].eq("not_started")]
    elif focus == "Com resolucao" and "hasSolutionResolution" in q.columns:
        q = q[q["hasSolutionResolution"].fillna(False)]
    elif focus == "Sem resolucao" and "hasSolutionResolution" in q.columns:
        q = q[~q["hasSolutionResolution"].fillna(False)]
    elif focus == "Ja visto em evento" and "eventsStarted" in q.columns:
        q = q[q["eventsStarted"].fillna(0) > 0]

    return q


def _progress_form(row: pd.Series):
    db = Database()
    challenge_id = row.get("challengeId")
    st.markdown("<div class='card'><h2 class='section-title'>Atualizar acompanhamento</h2>", unsafe_allow_html=True)
    st.caption(row.get("title") or challenge_id)

    labels = list(STATUS_LABELS.values())
    current_label = STATUS_LABELS.get(row.get("status"), "Nao iniciado")
    status_index = labels.index(current_label) if current_label in labels else 0

    with st.form("progress_form"):
        c1, c2, c3, c4 = st.columns(4)
        status_label = c1.selectbox("Status", labels, index=status_index)
        personal_difficulty = c2.slider("Dificuldade pessoal", 0, 5, int(row.get("personalDifficulty") or 0))
        time_spent = c3.number_input("Tempo gasto (min)", min_value=0, value=int(row.get("timeSpentMinutes") or 0), step=5)
        attempts = c4.number_input("Tentativas", min_value=0, value=int(row.get("attempts") or 0), step=1)

        c5, c6 = st.columns(2)
        last_practiced = c5.date_input("Ultimo treino", value=date.today())
        target_review = c6.date_input("Proxima revisao", value=date.today())
        blockers = st.text_input("Dificuldades principais", value=row.get("blockers") or "")
        notes = st.text_area("Notas de aprendizado", value=row.get("notes") or "", height=120)
        st.caption(
            f"Correcao: {', '.join(row.get('validationKinds_list') or []) or 'unknown'} | "
            f"input={int(row.get('numInputTasks') or 0)} lambda={int(row.get('numLambdaTasks') or 0)} ia={int(row.get('numAiTasks') or 0)}"
        )

        submitted = st.form_submit_button("Salvar progresso", use_container_width=True)

    if submitted:
        db.upsert_progress(
            challenge_id,
            {
                "status": STATUS_BY_LABEL[status_label],
                "personalDifficulty": personal_difficulty,
                "timeSpentMinutes": time_spent,
                "attempts": attempts,
                "lastPracticedAt": last_practiced.isoformat(),
                "targetReviewAt": target_review.isoformat(),
                "blockers": blockers,
                "notes": notes,
            },
        )
        st.cache_data.clear()
        st.success("Progresso salvo.")
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render(df: pd.DataFrame):
    render_header("Explorar", "Catalogo pesquisavel e acompanhamento individual")

    if df.empty:
        st.warning("Nenhum desafio encontrado. Execute a sincronizacao primeiro.")
        return

    q = _filter_df(df)
    st.caption(f"{len(q)} de {len(df)} desafios encontrados")

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("<div class='card'><h2 class='section-title'>Resultados</h2>", unsafe_allow_html=True)
        options = q["challengeId"].head(250).tolist()
        label_map = {
            row["challengeId"]: f"{row.get('title') or 'Sem titulo'} | {row.get('effectiveStatusLabel') or row.get('statusLabel')} | {row.get('solutionStatusLabel', 'Sem resolucao')}"
            for _, row in q.head(250).iterrows()
        }
        selected_id = st.selectbox(
            "Selecionar desafio",
            options,
            format_func=lambda value: label_map.get(value, value),
        ) if options else None

        for _, row in q.head(25).iterrows():
            st.markdown(
                render_challenge_card(
                    row.get("title"),
                    row.get("tags_list") or [],
                    int(row.get("difficulty") or 0),
                    int(row.get("avgSolveSeconds") or 0),
                    row.get("services_list") or [],
                    row.get("effectiveStatus") or row.get("status"),
                    int(row.get("personalDifficulty") or 0),
                    int(row.get("timeSpentMinutes") or 0),
                    bool(row.get("hasSolutionResolution") or False),
                    row.get("solutionStorageLabel") or "",
                ),
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        if selected_id:
            row = df[df["challengeId"].eq(selected_id)].iloc[0]
            _progress_form(row)
            if row.get("hasSolutionResolution"):
                st.success(f"{row.get('solutionStatusLabel')}: {row.get('solutionReference')}")
            else:
                st.warning("Este jam ainda nao tem resolucao mapeada no Git.")
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown("<div class='card'><h2 class='section-title'>Tasks e correcao</h2>", unsafe_allow_html=True)
            tasks = row.get("tasks") or []
            if tasks:
                task_rows = [
                    {
                        "Task": task.get("taskNumber"),
                        "Titulo": task.get("title"),
                        "Correcao": task.get("validationKind"),
                        "Input": task.get("allowInputAnswer"),
                        "Lambda": task.get("validatedByLambda"),
                        "Pontos": task.get("scorePercent"),
                    }
                    for task in tasks
                ]
                st.dataframe(pd.DataFrame(task_rows), use_container_width=True, hide_index=True)
            else:
                st.info("Este challenge ainda nao tem tasks detalhadas. Rode Sync full.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Nenhum resultado para editar.")
