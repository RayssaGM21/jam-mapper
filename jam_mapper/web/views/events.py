"""Events and report aggregation page."""

import pandas as pd
import streamlit as st

from jam_mapper.core.client import JamClient
from jam_mapper.core.db import Database
from jam_mapper.web.components.layout import render_header
from jam_mapper.web.context import sync_reports_from_ids


def render(df: pd.DataFrame):
    render_header("Eventos", "Historico de competicoes e consolidacao de reports")

    client = JamClient()
    db = Database()

    st.markdown("<div class='card'><h2 class='section-title'>Eventos disponiveis</h2>", unsafe_allow_html=True)
    try:
        events_payload = client.list_events_past()
        events = events_payload.get("events", []) if isinstance(events_payload, dict) else []
    except Exception as exc:
        events = db.list_events()
        if "401" in str(exc):
            st.info("Token expirado ou sem permissao. Usando eventos/reports salvos localmente.")
        else:
            st.info(f"API indisponivel agora. Usando dados locais quando existirem. Detalhe: {exc}")

    if events:
        ev_df = pd.json_normalize(events).reset_index(drop=True)
        visible_cols = [
            col
            for col in [
                "eventId",
                "title",
                "startTime",
                "endTime",
                "progress.totalChallenges",
                "progress.solvedChallenges",
                "totalChallenges",
                "solvedChallenges",
            ]
            if col in ev_df.columns
        ]
        st.dataframe(ev_df[visible_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum evento local encontrado. Atualize o token ou cole um eventId manual abaixo quando souber o ID.")
    st.markdown("</div>", unsafe_allow_html=True)

    if not events:
        return

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h2 class='section-title'>Analise consolidada</h2>", unsafe_allow_html=True)
    options = [f"{e.get('title') or 'Evento'} ({e.get('eventId')})" for e in events if e.get("eventId")]
    selected = st.multiselect("Eventos para agregar", options, default=options[: min(3, len(options))])
    selected_ids = [item.split("(")[-1].rstrip(")") for item in selected]
    manual_ids = st.text_area(
        "IDs manuais de eventos",
        placeholder="Um eventId por linha, ex.: 3968ed16-8162-451e-af2e-43a380614a8c",
        height=90,
    )
    selected_ids += [line.strip() for line in manual_ids.splitlines() if line.strip()]

    reports = []
    if st.button("Sincronizar reports selecionados", use_container_width=True) and selected_ids:
        sync_reports_from_ids(selected_ids)

    for event_id in selected_ids:
        report = db.get_event_report(event_id)
        if report is not None:
            reports.append(report)

    if reports:
        total_seen = 0
        solved = 0
        clues = 0
        rows = {}
        for report in reports:
            for challenge in report.get("challenges", []):
                total_seen += 1
                cid = challenge.get("id") or challenge.get("challengeId")
                if not cid:
                    continue
                row = rows.setdefault(
                    cid,
                    {
                        "Challenge": cid,
                        "Titulo": challenge.get("title"),
                        "Visto": 0,
                        "Resolvido": 0,
                        "Pontos": 0,
                        "Dicas": 0,
                    },
                )
                was_solved = bool(challenge.get("solved") or challenge.get("completed"))
                row["Visto"] += 1
                row["Resolvido"] += int(was_solved)
                row["Pontos"] += int(challenge.get("earnedPoints") or 0)
                row["Dicas"] += int(challenge.get("cluesUsed") or 0)
                solved += int(was_solved)
                clues += int(challenge.get("cluesUsed") or 0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Eventos", len(reports))
        c2.metric("Challenges vistos", total_seen)
        c3.metric("Resolvidos", solved)
        c4.metric("Dicas usadas", clues)

        if rows:
            result = pd.DataFrame(rows.values()).sort_values(["Resolvido", "Visto"], ascending=False)
            st.dataframe(result, use_container_width=True, hide_index=True)
    else:
        st.caption("Selecione eventos e carregue reports para ver metricas pessoais vindas da AWS.")
    st.markdown("</div>", unsafe_allow_html=True)
