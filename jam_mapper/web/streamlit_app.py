"""AWS Jam Performance Hub main application."""

import inspect
import logging

import pandas as pd
import streamlit as st

from jam_mapper.web.components.layout import render_sidebar
from jam_mapper.web.auth import require_authenticated_user
from jam_mapper.core.config import get_settings
from jam_mapper.core.token import get_runtime_authorization_token
from jam_mapper.web.context import load_challenges, load_events, merge_report_metrics
from jam_mapper.web.theme import inject_theme
from jam_mapper.web.views import dashboard, events, explore, notes, performance, resolution, settings, training


logger = logging.getLogger("jam_mapper.web")


st.set_page_config(
    page_title="AWS Jam Performance Hub",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

user = require_authenticated_user()

if not st.session_state.get("aws_session_ready"):
    settings = get_settings()
    if settings.token_refresh_enabled:
        try:
            with st.spinner("Conectando com segurança à AWS Jam..."):
                get_runtime_authorization_token(force=True)
        except Exception as exc:
            logger.exception("AWS Jam session initialization failed: %s", exc)
            st.warning("Não foi possível atualizar a sessão da AWS Jam automaticamente; usando o token configurado.")
    else:
        get_runtime_authorization_token(force=True)
    st.session_state.aws_session_ready = True

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
    sync_notice = st.session_state.pop("sync_notice", None)
    if sync_notice:
        st.success(sync_notice)

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

    render_sidebar(events_list, user=user)

    if df.empty:
        st.warning(
            "O banco desta instância está vazio. No Streamlit Cloud isso é esperado "
            "na primeira execução ou após a aplicação reiniciar."
        )
        if st.button("Sincronizar dados agora", type="primary"):
            from jam_mapper.web.context import run_sync

            run_sync(full=False)
        return

    render_page(df)


if __name__ == "__main__":
    main()
