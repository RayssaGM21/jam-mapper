"""AWS Jam Performance Hub main application."""

import inspect

import pandas as pd
import streamlit as st

from jam_mapper.web.components.layout import render_sidebar
from jam_mapper.web.context import load_challenges, load_events, merge_report_metrics
from jam_mapper.web.theme import inject_theme
from jam_mapper.web.views import dashboard, events, explore, notes, performance, resolution, settings, training


st.set_page_config(
    page_title="AWS Jam Performance Hub",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "selected_event" not in st.session_state:
    st.session_state.selected_event = None


def render_page(df: pd.DataFrame):
    routes = {
        "Dashboard": dashboard,
        "Explorar": explore,
        "Performance": performance,
        "Eventos": events,
        "Treino": training,
        "Resolucao": resolution,
        "Notas": notes,
        "Configuracoes": settings,
    }

    render_fn = routes.get(st.session_state.page)
    if not render_fn:
        st.error("Pagina nao encontrada")
        return

    params = inspect.signature(render_fn).parameters
    if "selected_event" in params:
        render_fn(df=df, selected_event=st.session_state.selected_event)
    else:
        render_fn(df)


def main():
    loader = st.empty()
    loader.markdown(
        """
        <div class="app-loading-overlay">
            <div class="app-loading-panel">
                <div class="app-loading-spinner"></div>
                <div class="app-loading-title">Carregando dados</div>
                <div class="app-loading-subtitle">Preparando catalogo, reports e metricas</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    df = merge_report_metrics(load_challenges())
    events_list = load_events()
    loader.empty()

    render_sidebar(events_list)

    if df.empty:
        st.warning("Nenhum desafio encontrado. Execute a sincronizacao.")
        return

    render_page(df)


if __name__ == "__main__":
    main()
