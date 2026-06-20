"""Layout helpers for the web interface."""

from typing import Any, Dict, List
from pathlib import Path
import base64

import streamlit as st

from jam_mapper.web.theme import render_header as theme_render_header


def render_header(title: str, subtitle: str = ""):
    return theme_render_header(title, subtitle)


def _sidebar_logo_html() -> str:
    logo_path = Path(__file__).resolve().parents[3] / "assets" / "jam-logo.png"
    if not logo_path.exists():
        return ""
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return (
        "<div class='sidebar-logo-wrap'>"
        f"<img class='sidebar-logo' src='data:image/png;base64,{encoded}' alt='AWS Jam Hub logo'>"
        "</div>"
    )


def render_sidebar(events_list: List[Dict[str, Any]], user=None):
    with st.sidebar:
        st.markdown(_sidebar_logo_html(), unsafe_allow_html=True)
        st.markdown(
            """
            <div class='sidebar-brand'>
                <div class='app-title'>AWS Jam Hub</div>
                <div class='app-subtitle'>WorldSkills tracker</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown("<div class='sidebar-section-title'>Navegacao</div>", unsafe_allow_html=True)

        pages = [
            "Dashboard",
            "Explorar",
            "Performance",
            "Eventos",
            "Treino",
            "Resolucao",
            "Notas",
            "Configuracoes",
        ]

        current = st.session_state.get("page", "Dashboard")
        default_index = pages.index(current) if current in pages else 0
        st.session_state.page = st.radio("Menu", pages, index=default_index, key="main_nav", label_visibility="collapsed")

        st.divider()

        def event_label(event: Dict[str, Any]) -> str:
            title = event.get("title") or "Evento"
            event_id = event.get("eventId") or ""
            label = f"{title} - {event_id}" if event_id else title
            return label if len(label) <= 42 else f"{label[:39]}..."

        event_options = ["Todos"] + [event_label(e) for e in events_list]
        selected = st.selectbox("Evento em foco", event_options, index=0)
        st.session_state.selected_event = None if selected == "Todos" else selected

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sync rapido", use_container_width=True):
                from jam_mapper.web.context import run_sync

                run_sync(full=False)
        with col2:
            if st.button("Sync full", use_container_width=True):
                from jam_mapper.web.context import run_sync

                run_sync(full=True)

        st.divider()
        if user:
            st.caption(user.email)
            if st.button("Sair", use_container_width=True):
                from jam_mapper.web.auth import logout

                logout()
        st.markdown("<div class='sidebar-footer'>v1.2 | AWS Jam tracker</div>", unsafe_allow_html=True)
