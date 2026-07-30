"""Markdown solution documentation page."""

from pathlib import Path
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from jam_mapper.core.db import Database
from jam_mapper.core.github_storage import GitHubSolutionStorage
from jam_mapper.core.solutions import build_solution_template, ensure_solution_file
from jam_mapper.web.components.layout import render_header


_live_markdown_editor = components.declare_component(
    "live_markdown_editor",
    path=str(Path(__file__).resolve().parents[1] / "components" / "markdown_live_editor"),
)


def _selected_row(df: pd.DataFrame, challenge_id: str):
    rows = df[df["challengeId"].eq(challenge_id)]
    return rows.iloc[0] if not rows.empty else None


def _load_github_solution(challenge_id: str, challenge: dict):
    storage = GitHubSolutionStorage()
    remote = storage.read(challenge_id)
    if remote:
        return remote.content, remote.sha, remote.html_url, remote.path, True

    content = build_solution_template(challenge)
    return content, None, None, storage.solution_path(challenge_id), False


def _editor_key(active_id: str, storage_mode: str) -> str:
    return f"solution_editor_{storage_mode.lower()}_{active_id}"


def _saved_key(active_id: str, storage_mode: str) -> str:
    return f"solution_saved_{storage_mode.lower()}_{active_id}"


def _textarea_key(editor_key: str) -> str:
    return f"{editor_key}_textarea"


def _hydrate_editor(active_id: str, storage_mode: str, content: str):
    key = _editor_key(active_id, storage_mode)
    saved = _saved_key(active_id, storage_mode)
    if key not in st.session_state:
        st.session_state[key] = content
    if saved not in st.session_state:
        st.session_state[saved] = content
    return key, saved


def _sync_textarea_from_editor(editor_key: str):
    textarea_key = _textarea_key(editor_key)
    current = st.session_state.get(editor_key, "")
    if st.session_state.get(textarea_key) != current:
        st.session_state[textarea_key] = current
    return textarea_key


def _render_markdown_preview(content: str, height: int = 520):
    with st.container(height=height, border=True):
        if not content.strip():
            st.info("Preview vazio.")
            return
        st.markdown(content)


def _autosave_local(path: Path, edited: str, saved_key: str):
    if edited == st.session_state.get(saved_key):
        return
    path.write_text(edited, encoding="utf-8")
    st.session_state[saved_key] = edited
    st.session_state.solution_autosave_notice = f"Salvo automaticamente as {time.strftime('%H:%M:%S')}."


def _autosave_github(github_storage: GitHubSolutionStorage, db: Database, active_id: str, edited: str, saved_key: str):
    if edited == st.session_state.get(saved_key):
        return
    saved = github_storage.write(
        active_id,
        edited,
        message=f"docs: autosave solution for {active_id}",
        sha=st.session_state.get("solution_sha"),
    )
    st.session_state.solution_content = edited
    st.session_state.solution_sha = saved.sha
    st.session_state.solution_remote_url = saved.html_url
    st.session_state.solution_storage_path = saved.path
    st.session_state[saved_key] = edited
    st.session_state.solution_autosave_notice = f"Salvo automaticamente no GitHub as {time.strftime('%H:%M:%S')}."
    db.upsert_progress(active_id, {"solutionMarkdownPath": f"github:{saved.path}"})
    st.cache_data.clear()


def _component_content(value):
    if isinstance(value, dict):
        return str(value.get("content") or ""), bool(value.get("shouldSave"))
    if isinstance(value, str):
        return value, True
    return None, False


@st.dialog("Editor expandido", width="large")
def _expanded_markdown_editor(editor_key: str, saved_key: str, storage_mode: str, active_id: str, selected_path: str = ""):
    db = Database()
    expanded_key = f"{editor_key}_expanded"
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = st.session_state.get(editor_key, "")

    component_value = _live_markdown_editor(
        value=st.session_state.get(expanded_key, ""),
        key=f"{expanded_key}_component",
        default=st.session_state.get(expanded_key, ""),
    )
    edited, should_save = _component_content(component_value)
    if edited is not None:
        st.session_state[expanded_key] = edited
        st.session_state[editor_key] = edited
        if not should_save:
            return
        if storage_mode == "github":
            github_storage = GitHubSolutionStorage()
            try:
                _autosave_github(github_storage, db, active_id, edited, saved_key)
            except Exception as exc:
                st.error(f"Falha no salvamento automatico no GitHub: {exc}")
        else:
            try:
                _autosave_local(Path(selected_path), edited, saved_key)
            except Exception as exc:
                st.error(f"Falha no salvamento automatico local: {exc}")
        if st.session_state.get("solution_autosave_notice"):
            st.caption(st.session_state.solution_autosave_notice)


def render(df: pd.DataFrame):
    render_header("Resolucao", "Documente o passo a passo de cada AWS Jam")

    if df.empty:
        st.warning("Nenhum desafio encontrado. Execute a sincronizacao.")
        return

    db = Database()
    github_storage = GitHubSolutionStorage()
    storage_mode = "GitHub" if github_storage.enabled else "Local"
    left, right = st.columns([1, 1.2])

    with left:
        st.markdown("<div class='card'><h2 class='section-title'>Escolher desafio</h2>", unsafe_allow_html=True)
        st.caption(f"Armazenamento atual: {storage_mode}")
        search = st.text_input("Buscar", placeholder="Nome, ID, tag ou servico")
        q = df.copy()
        if search:
            text = search.lower()
            q = q[
                q["challengeId"].fillna("").str.lower().str.contains(text)
                | q["title"].fillna("").str.lower().str.contains(text)
                | q["tags_list"].apply(lambda values: any(text in str(v).lower() for v in values))
                | q["services_list"].apply(lambda values: any(text in str(v).lower() for v in values))
            ]

        status_col = "effectiveStatus" if "effectiveStatus" in q.columns else "status"
        label_col = "effectiveStatusLabel" if "effectiveStatusLabel" in q.columns else "statusLabel"
        q = q.sort_values([status_col, "difficulty", "title"], ascending=[True, False, True])
        options = q["challengeId"].head(500).tolist()
        labels = {
            row["challengeId"]: f"{row.get('title') or row['challengeId']} | {row.get(label_col)} | {row.get('solutionStatusLabel', 'Sem resolucao')} | input {int(row.get('numInputTasks') or 0)}"
            for _, row in q.head(500).iterrows()
        }
        selected_id = st.selectbox("Challenge", options, format_func=lambda value: labels.get(value, value)) if options else None

        if selected_id:
            row = _selected_row(df, selected_id)
            st.caption(f"ID: {selected_id}")
            st.caption(f"Correcao: {', '.join(row.get('validationKinds_list') or []) or 'unknown'}")
            if st.button("Criar/abrir Markdown", use_container_width=True):
                challenge = db.get_challenge(selected_id) or row.to_dict()
                if github_storage.enabled:
                    try:
                        content, sha, html_url, path, exists_remote = _load_github_solution(selected_id, challenge)
                        st.session_state.solution_content = content
                        st.session_state.solution_sha = sha
                        st.session_state.solution_remote_url = html_url
                        st.session_state.solution_storage_path = path
                        st.session_state.solution_challenge_id = selected_id
                        editor_key = _editor_key(selected_id, "github")
                        saved_key = _saved_key(selected_id, "github")
                        st.session_state[editor_key] = content
                        st.session_state[saved_key] = content
                        if exists_remote:
                            db.upsert_progress(selected_id, {"solutionMarkdownPath": f"github:{path}"})
                            st.success(f"Markdown pronto no GitHub: {path}")
                        else:
                            st.info("Template carregado. O arquivo so sera criado no GitHub quando voce alterar o texto.")
                    except Exception as exc:
                        st.error(f"Falha ao abrir/salvar no GitHub: {exc}")
                else:
                    path = ensure_solution_file(selected_id)
                    st.session_state.solution_path = str(path)
                    st.session_state.solution_challenge_id = selected_id
                    content = path.read_text(encoding="utf-8")
                    editor_key = _editor_key(selected_id, "local")
                    saved_key = _saved_key(selected_id, "local")
                    st.session_state[editor_key] = content
                    st.session_state[saved_key] = content
                    st.success(f"Arquivo pronto: {path}")
                st.cache_data.clear()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown("<div class='card'><h2 class='section-title'>Cobertura</h2>", unsafe_allow_html=True)
        if github_storage.enabled:
            st.info("No modo GitHub, a cobertura e conferida ao abrir cada resolucao.")
        else:
            documented = 0
            for challenge_id in df["challengeId"].dropna():
                progress = db.get_progress(challenge_id) or {}
                path = progress.get("solutionMarkdownPath")
                if path and Path(path).exists():
                    documented += 1
            st.metric("Arquivos Markdown", documented)
            st.metric("Faltam documentar", max(0, len(df) - documented))
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'><h2 class='section-title'>Editor Markdown</h2>", unsafe_allow_html=True)
        active_id = st.session_state.get("solution_challenge_id")

        if github_storage.enabled:
            content = st.session_state.get("solution_content")
            if active_id and content is not None:
                editor_key, saved_key = _hydrate_editor(active_id, "github", content)
                if st.button("Expandir editor", use_container_width=True):
                    st.session_state[f"{editor_key}_expanded"] = st.session_state.get(editor_key, "")
                    _expanded_markdown_editor(editor_key, saved_key, "github", active_id)
                tabs = st.tabs(["Editor", "Preview"])
                with tabs[0]:
                    textarea_key = _sync_textarea_from_editor(editor_key)
                    edited = st.text_area("Conteudo", key=textarea_key, height=520)
                    st.session_state[editor_key] = edited
                    try:
                        _autosave_github(github_storage, db, active_id, edited, saved_key)
                    except Exception as exc:
                        st.error(f"Falha no salvamento automatico no GitHub: {exc}")
                    if st.session_state.get("solution_autosave_notice"):
                        st.caption(st.session_state.solution_autosave_notice)
                with tabs[1]:
                    _render_markdown_preview(st.session_state.get(editor_key, ""))
                c1, c2 = st.columns(2)
                if c1.button("Salvar no GitHub", use_container_width=True):
                    try:
                        edited = st.session_state.get(editor_key, "")
                        if edited == st.session_state.get(saved_key):
                            st.info("Nada para salvar. O arquivo nao foi criado/alterado no GitHub.")
                        else:
                            saved = github_storage.write(
                                active_id,
                                edited,
                                message=f"docs: update solution for {active_id}",
                                sha=st.session_state.get("solution_sha"),
                            )
                            st.session_state.solution_content = edited
                            st.session_state.solution_sha = saved.sha
                            st.session_state.solution_remote_url = saved.html_url
                            st.session_state.solution_storage_path = saved.path
                            db.upsert_progress(active_id, {"solutionMarkdownPath": f"github:{saved.path}"})
                            st.session_state[saved_key] = edited
                            st.cache_data.clear()
                            st.success("Resolucao salva no GitHub.")
                    except Exception as exc:
                        st.error(f"Falha ao salvar no GitHub: {exc}")
                with c2:
                    st.download_button(
                        "Baixar Markdown",
                        st.session_state.get(editor_key, ""),
                        file_name=f"{active_id}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                if st.session_state.get("solution_remote_url"):
                    st.markdown(f"[Abrir no GitHub]({st.session_state.solution_remote_url})")
                st.caption(st.session_state.get("solution_storage_path", ""))
            else:
                st.info("Clique em Criar/abrir Markdown para carregar uma resolucao do GitHub.")
        else:
            selected_path = st.session_state.get("solution_path")
            if active_id and not selected_path:
                progress = db.get_progress(active_id) or {}
                selected_path = progress.get("solutionMarkdownPath")

            if selected_path and Path(selected_path).exists():
                path = Path(selected_path)
                content = path.read_text(encoding="utf-8")
                editor_key, saved_key = _hydrate_editor(active_id, "local", content)
                if st.button("Expandir editor", use_container_width=True):
                    st.session_state[f"{editor_key}_expanded"] = st.session_state.get(editor_key, "")
                    _expanded_markdown_editor(editor_key, saved_key, "local", active_id, str(path))
                tabs = st.tabs(["Editor", "Preview"])
                with tabs[0]:
                    textarea_key = _sync_textarea_from_editor(editor_key)
                    edited = st.text_area("Conteudo", key=textarea_key, height=520)
                    st.session_state[editor_key] = edited
                    try:
                        _autosave_local(path, edited, saved_key)
                    except Exception as exc:
                        st.error(f"Falha no salvamento automatico local: {exc}")
                    if st.session_state.get("solution_autosave_notice"):
                        st.caption(st.session_state.solution_autosave_notice)
                with tabs[1]:
                    _render_markdown_preview(st.session_state.get(editor_key, ""))
                c1, c2 = st.columns(2)
                if c1.button("Salvar Markdown", use_container_width=True):
                    edited = st.session_state.get(editor_key, "")
                    path.write_text(edited, encoding="utf-8")
                    st.session_state[saved_key] = edited
                    st.success("Resolucao salva.")
                with c2:
                    st.download_button(
                        "Baixar Markdown",
                        st.session_state.get(editor_key, ""),
                        file_name=path.name,
                        mime="text/markdown",
                        use_container_width=True,
                    )
                st.caption(str(path))
            else:
                st.info("Clique em Criar/abrir Markdown para gerar o template deste desafio.")
        st.markdown("</div>", unsafe_allow_html=True)
