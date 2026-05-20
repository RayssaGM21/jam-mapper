"""Persistent notes page."""

import streamlit as st

from jam_mapper.core.db import Database
from jam_mapper.web.components.layout import render_header


def render(df):
    render_header("Notas", "Diario rapido de estudo, erros recorrentes e revisoes")
    db = Database()
    saved = db.get_setting("global_notes", "")

    st.markdown("<div class='card'><h2 class='section-title'>Caderno de treino</h2>", unsafe_allow_html=True)
    notes = st.text_area(
        "Anotacoes",
        value=saved,
        height=360,
        placeholder="Ex.: IAM roles ainda confundem em Lambda; revisar VPC endpoints; refazer labs de S3 policy.",
    )
    c1, c2 = st.columns([1, 4])
    if c1.button("Salvar", use_container_width=True):
        db.set_setting("global_notes", notes)
        st.success("Notas salvas.")
    c2.caption("Use este espaco para registrar padroes de erro e decisoes que voce quer lembrar antes dos proximos jams.")
    st.markdown("</div>", unsafe_allow_html=True)
