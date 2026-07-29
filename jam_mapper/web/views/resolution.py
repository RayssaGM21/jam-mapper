"""Markdown solution documentation page."""

from pathlib import Path

import pandas as pd
import streamlit as st

from jam_mapper.core.db import Database
from jam_mapper.core.github_storage import GitHubSolutionStorage
from jam_mapper.core.solutions import build_solution_template, ensure_solution_file
from jam_mapper.web.components.layout import render_header


def _selected_row(df: pd.DataFrame, challenge_id: str):
    rows = df[df["challengeId"].eq(challenge_id)]
    return rows.iloc[0] if not rows.empty else None


def _load_github_solution(challenge_id: str, challenge: dict):
    storage = GitHubSolutionStorage()
    remote = storage.read(challenge_id)
    if remote:
        return remote.content, remote.sha, remote.html_url, remote.path

    content = build_solution_template(challenge)
    created = storage.write(
        challenge_id,
        content,
        message=f"docs: create solution for {challenge_id}",
    )
    return created.content, created.sha, created.html_url, created.path


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
                        content, sha, html_url, path = _load_github_solution(selected_id, challenge)
                        st.session_state.solution_content = content
                        st.session_state.solution_sha = sha
                        st.session_state.solution_remote_url = html_url
                        st.session_state.solution_storage_path = path
                        st.session_state.solution_challenge_id = selected_id
                        db.upsert_progress(selected_id, {"solutionMarkdownPath": f"github:{path}"})
                        st.success(f"Markdown pronto no GitHub: {path}")
                    except Exception as exc:
                        st.error(f"Falha ao abrir/salvar no GitHub: {exc}")
                else:
                    path = ensure_solution_file(selected_id)
                    st.session_state.solution_path = str(path)
                    st.session_state.solution_challenge_id = selected_id
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
                edited = st.text_area("Conteudo", value=content, height=520)
                c1, c2 = st.columns(2)
                if c1.button("Salvar no GitHub", use_container_width=True):
                    try:
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
                        st.cache_data.clear()
                        st.success("Resolucao salva no GitHub.")
                    except Exception as exc:
                        st.error(f"Falha ao salvar no GitHub: {exc}")
                with c2:
                    st.download_button(
                        "Baixar Markdown",
                        edited,
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
                edited = st.text_area("Conteudo", value=content, height=520)
                c1, c2 = st.columns(2)
                if c1.button("Salvar Markdown", use_container_width=True):
                    path.write_text(edited, encoding="utf-8")
                    st.success("Resolucao salva.")
                with c2:
                    st.download_button(
                        "Baixar Markdown",
                        edited,
                        file_name=path.name,
                        mime="text/markdown",
                        use_container_width=True,
                    )
                st.caption(str(path))
            else:
                st.info("Clique em Criar/abrir Markdown para gerar o template deste desafio.")
        st.markdown("</div>", unsafe_allow_html=True)
