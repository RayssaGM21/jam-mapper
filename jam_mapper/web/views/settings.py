"""Settings and data health page."""

from pathlib import Path

import streamlit as st

from jam_mapper.core.config import get_settings
from jam_mapper.core.db import Database
from jam_mapper.web.components.layout import render_header


def render(df):
    render_header("Configuracoes", "Saude dos dados e preferencias locais")

    settings = get_settings()
    db = Database()

    c1, c2, c3 = st.columns(3)
    c1.metric("Challenges", len(df))
    c2.metric("Registros pessoais", len(db.list_progress()))
    c3.metric("Eventos no banco", len(db.list_events()))

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h2 class='section-title'>Caminhos</h2>", unsafe_allow_html=True)
    st.code(
        "\n".join(
            [
                f"Banco SQLite: {Path(settings.sqlite_path).resolve()}",
                f"Exportacoes: {Path(settings.export_path).resolve()}",
                f"API base: {settings.base_url}",
            ]
        )
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h2 class='section-title'>Preferencias</h2>", unsafe_allow_html=True)
    weekly_goal = int(db.get_setting("weekly_goal", 8))
    review_days = int(db.get_setting("review_days", 7))

    with st.form("settings_form"):
        new_weekly_goal = st.number_input("Meta semanal de jams", min_value=1, max_value=100, value=weekly_goal)
        new_review_days = st.number_input("Intervalo padrao de revisao (dias)", min_value=1, max_value=90, value=review_days)
        saved = st.form_submit_button("Salvar preferencias")

    if saved:
        db.set_setting("weekly_goal", int(new_weekly_goal))
        db.set_setting("review_days", int(new_review_days))
        st.success("Preferencias salvas.")
    st.markdown("</div>", unsafe_allow_html=True)
