"""Markdown solution document helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from jam_mapper.core.config import get_settings
from jam_mapper.core.db import Database


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\-]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-") or "challenge"


def solutions_dir() -> Path:
    return Path(get_settings().export_path).resolve() / "solutions"


def solution_path(challenge_id: str) -> Path:
    return solutions_dir() / f"{slugify(challenge_id)}.md"


def build_solution_template(challenge: Dict[str, Any]) -> str:
    title = challenge.get("title") or challenge.get("challengeId")
    services = ", ".join(challenge.get("awsServices") or [])
    tags = ", ".join(challenge.get("tags") or [])
    validation = ", ".join(challenge.get("validationKinds") or [])
    tasks = challenge.get("tasks") or []

    task_lines = []
    for task in tasks:
        task_lines.append(
            "\n".join(
                [
                    f"### Task {task.get('taskNumber')}: {task.get('title') or 'Sem titulo'}",
                    "",
                    f"- Correcao: `{task.get('validationKind') or 'unknown'}`",
                    f"- Campo de resposta: {'sim' if task.get('allowInputAnswer') else 'nao'}",
                    f"- Pontos: {task.get('scorePercent') or 0}%",
                    "",
                    "#### Resolucao",
                    "",
                    "- ",
                    "",
                    "#### Comandos / evidencias",
                    "",
                    "```bash",
                    "# comandos usados",
                    "```",
                    "",
                    "#### Erros encontrados",
                    "",
                    "- ",
                ]
            )
        )

    task_section = "\n\n".join(task_lines) if task_lines else "Nenhuma task detalhada sincronizada ainda."

    return f"""# {title}

## Identificacao

- Challenge ID: `{challenge.get('challengeId')}`
- Categoria: {challenge.get('category') or ''}
- Dificuldade AWS: {challenge.get('difficulty') or ''}
- Tipo Jam: {challenge.get('jamType') or ''}
- Correcao detectada: {validation or 'unknown'}
- Servicos: {services}
- Tags: {tags}

## Objetivo

Descreva em uma frase o que o desafio pede e qual arquitetura/servico ele treina.

## Estrategia rapida

1. 
2. 
3. 

## Passo a passo

{task_section}

## Checklist de revisao

- [ ] Sei explicar o problema sem olhar o enunciado.
- [ ] Sei encontrar rapidamente os recursos no console.
- [ ] Sei validar cada task sem tentativa aleatoria.
- [ ] Tenho comandos ou evidencias reutilizaveis.

## Resumo para competicao

- Atalho mental:
- Risco comum:
- Tempo alvo:
"""


def ensure_solution_file(challenge_id: str) -> Path:
    db = Database()
    challenge = db.get_challenge(challenge_id)
    if not challenge:
        raise ValueError(f"Challenge nao encontrado: {challenge_id}")

    path = solution_path(challenge_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(build_solution_template(challenge), encoding="utf-8")

    progress = db.get_progress(challenge_id) or {}
    if progress.get("solutionMarkdownPath") != str(path):
        db.upsert_progress(challenge_id, {"solutionMarkdownPath": str(path)})

    return path
