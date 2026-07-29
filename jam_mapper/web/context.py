"""Shared data and app utilities for the Streamlit interface."""

from typing import Any, Dict, List
import json

import pandas as pd
import streamlit as st

from jam_mapper.core.client import JamClient
from jam_mapper.core.db import Database
from jam_mapper.core.github_storage import GitHubSolutionStorage
from jam_mapper.core.solutions import solution_path


STATUS_LABELS = {
    "not_started": "Nao iniciado",
    "in_progress": "Em andamento",
    "done": "Concluido",
    "review": "Revisar",
}


@st.cache_data(ttl=120)
def load_challenges() -> pd.DataFrame:
    db = Database()
    challenges = db.list_challenges()
    if not challenges:
        return pd.DataFrame()

    df = pd.json_normalize(challenges)

    def normalize_list(value):
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [value]
            except Exception:
                return [value]
        return []

    if "tags" not in df.columns:
        df["tags"] = [[] for _ in range(len(df))]
    if "awsServices" not in df.columns:
        df["awsServices"] = [[] for _ in range(len(df))]

    df["tags_list"] = df["tags"].apply(normalize_list)
    df["services_list"] = df["awsServices"].apply(normalize_list)

    defaults = {
        "difficulty": 0,
        "numTasks": 0,
        "numInputTasks": 0,
        "numLambdaTasks": 0,
        "numAiTasks": 0,
        "avgSolveSeconds": 0,
        "passRate": 0,
        "difficultyRating": 0,
        "rating": 0,
        "totalIncorrect": 0,
        "totalRequestedClues": 0,
        "totalCorrect": 0,
        "stability": 0,
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
        df[col] = df[col].fillna(default)

    progress = pd.DataFrame(db.list_progress())
    if not progress.empty:
        df = df.merge(progress, on="challengeId", how="left")

    if "status" not in df.columns:
        df["status"] = "not_started"
    df["status"] = df["status"].fillna("not_started")
    for col in ["hasInputAnswer", "hasLambdaValidation", "hasAiValidation"]:
        if col not in df.columns:
            df[col] = False
        df[col] = df[col].fillna(False).astype(bool)
    if "validationKinds" not in df.columns:
        df["validationKinds"] = [[] for _ in range(len(df))]
    df["validationKinds_list"] = df["validationKinds"].apply(normalize_list)
    for col in ["personalDifficulty", "timeSpentMinutes", "attempts"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0).astype(int)
    for col in ["blockers", "notes"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")
    for col in ["lastPracticedAt", "targetReviewAt"]:
        if col not in df.columns:
            df[col] = None

    df["statusLabel"] = df["status"].map(STATUS_LABELS).fillna("Nao iniciado")
    df["is_done"] = df["status"].eq("done")
    df["needs_review"] = df["status"].eq("review")
    df["is_started"] = df["status"].isin(["in_progress", "done", "review"])
    df = add_solution_resolution_status(df)

    return df.reset_index(drop=True)


def add_solution_resolution_status(df: pd.DataFrame) -> pd.DataFrame:
    """Mark challenges that already have a solution document locally or in GitHub."""
    if df.empty:
        return df

    out = df.copy()
    if "solutionMarkdownPath" not in out.columns:
        out["solutionMarkdownPath"] = ""
    out["solutionMarkdownPath"] = out["solutionMarkdownPath"].fillna("")

    github_storage = GitHubSolutionStorage()
    github_paths: set[str] = set()
    if github_storage.enabled:
        try:
            github_paths = github_storage.list_solution_paths()
        except Exception:
            github_paths = set()

    def solution_state(row):
        challenge_id = row.get("challengeId")
        stored_path = str(row.get("solutionMarkdownPath") or "")
        expected_github_path = github_storage.solution_path(challenge_id) if challenge_id and github_storage.enabled else ""
        if expected_github_path and expected_github_path in github_paths:
            return True, "GitHub", expected_github_path
        if stored_path.startswith("github:"):
            return True, "GitHub", stored_path.removeprefix("github:")
        if stored_path and not stored_path.startswith("github:"):
            from pathlib import Path

            if Path(stored_path).exists():
                return True, "Local", stored_path
        if challenge_id:
            local_path = solution_path(str(challenge_id))
            if local_path.exists():
                return True, "Local", str(local_path)
        return False, "Sem resolucao", ""

    states = out.apply(solution_state, axis=1)
    out["hasSolutionResolution"] = states.apply(lambda value: value[0]).astype(bool)
    out["solutionStorageLabel"] = states.apply(lambda value: value[1])
    out["solutionReference"] = states.apply(lambda value: value[2])
    out["solutionStatusLabel"] = out["hasSolutionResolution"].map(
        {True: "Resolucao no Git", False: "Sem resolucao"}
    )
    out.loc[out["hasSolutionResolution"] & out["solutionStorageLabel"].eq("Local"), "solutionStatusLabel"] = "Resolucao local"
    return out


@st.cache_data(ttl=120)
def load_event_report_metrics() -> pd.DataFrame:
    """Flatten stored event reports into per-challenge personal metrics."""
    db = Database()
    reports = db.list_event_reports()
    rows = {}

    for report in reports:
        event_id = report.get("eventName") or report.get("eventId")
        event_title = report.get("eventTitle")
        for team in report.get("teamMetrics", []):
            team_name = team.get("teamName")
            for item in team.get("startedChallenges", []):
                challenge_id = item.get("challengeId")
                if not challenge_id:
                    continue
                row = rows.setdefault(
                    challenge_id,
                    {
                        "challengeId": challenge_id,
                        "eventsStarted": 0,
                        "eventsSolved": 0,
                        "eventTitles": set(),
                        "teamNames": set(),
                        "completedTasksFromReports": 0,
                        "incorrectAnswersFromReports": 0,
                        "cluesFromReports": 0,
                        "attemptsFromReports": 0,
                        "timeSpentFromReportsMinutes": 0,
                        "timeToFirstAttemptMs": [],
                        "timeToCompletedMs": [],
                        "feedbackComments": [],
                    },
                )
                row["eventsStarted"] += 1
                row["eventTitles"].add(event_title or event_id)
                row["teamNames"].add(team_name)
                row["completedTasksFromReports"] += int(item.get("numCompletedTasks") or 0)
                row["incorrectAnswersFromReports"] += int(item.get("numIncorrectAnswers") or 0)
                row["cluesFromReports"] += int(item.get("numCluesUsed") or 0)
                row["attemptsFromReports"] += int(item.get("totalNumberOfAttempts") or 0)
                if item.get("timeToFirstAttempt") is not None:
                    row["timeToFirstAttemptMs"].append(item.get("timeToFirstAttempt"))
                if item.get("timeToCompletedChallenge") is not None:
                    completed_ms = int(item.get("timeToCompletedChallenge") or 0)
                    row["timeToCompletedMs"].append(completed_ms)
                    row["timeSpentFromReportsMinutes"] += int(completed_ms / 60000)
                    row["eventsSolved"] += 1
                row["feedbackComments"].extend(str(comment) for comment in (item.get("feedbackComments") or []) if comment)

    output = []
    for row in rows.values():
        first = row.pop("timeToFirstAttemptMs")
        completed = row.pop("timeToCompletedMs")
        row["avgTimeToFirstAttemptSeconds"] = int(sum(first) / len(first) / 1000) if first else 0
        row["avgTimeToCompletedSeconds"] = int(sum(completed) / len(completed) / 1000) if completed else 0
        row["eventTitles"] = ", ".join(sorted(x for x in row["eventTitles"] if x))
        row["teamNames"] = ", ".join(sorted(x for x in row["teamNames"] if x))
        row["feedbackComments"] = "\n\n".join(row["feedbackComments"])
        output.append(row)

    return pd.DataFrame(output)


def merge_report_metrics(df: pd.DataFrame) -> pd.DataFrame:
    metrics = load_event_report_metrics()
    if metrics.empty:
        return add_effective_progress(df)
    merged = df.merge(metrics, on="challengeId", how="left")
    for col in [
        "eventsStarted",
        "eventsSolved",
        "completedTasksFromReports",
        "incorrectAnswersFromReports",
        "cluesFromReports",
        "attemptsFromReports",
        "timeSpentFromReportsMinutes",
        "avgTimeToFirstAttemptSeconds",
        "avgTimeToCompletedSeconds",
    ]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0).astype(int)
    for col in ["eventTitles", "teamNames", "feedbackComments"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna("")
    return add_effective_progress(merged)


def add_effective_progress(df: pd.DataFrame) -> pd.DataFrame:
    """Combine local progress with AWS event reports without overwriting local data."""
    if df.empty:
        return df

    out = df.copy()
    for col in ["eventsStarted", "eventsSolved", "timeSpentFromReportsMinutes", "attemptsFromReports", "cluesFromReports"]:
        if col not in out.columns:
            out[col] = 0
        out[col] = out[col].fillna(0).astype(int)

    def effective_status(row):
        local = row.get("status") or "not_started"
        if local and local != "not_started":
            return local
        if int(row.get("eventsSolved") or 0) > 0:
            return "done"
        if int(row.get("eventsStarted") or 0) > 0:
            return "in_progress"
        return "not_started"

    out["effectiveStatus"] = out.apply(effective_status, axis=1)
    out["effectiveStatusLabel"] = out["effectiveStatus"].map(STATUS_LABELS).fillna("Nao iniciado")
    out["effective_is_done"] = out["effectiveStatus"].eq("done")
    out["effective_needs_review"] = out["effectiveStatus"].eq("review")
    out["effective_is_started"] = out["effectiveStatus"].isin(["in_progress", "done", "review"])
    out["effectiveTimeSpentMinutes"] = out["timeSpentMinutes"].fillna(0).astype(int)
    out.loc[out["effectiveTimeSpentMinutes"].eq(0), "effectiveTimeSpentMinutes"] = out.loc[
        out["effectiveTimeSpentMinutes"].eq(0), "timeSpentFromReportsMinutes"
    ]
    out["effectiveAttempts"] = out["attempts"].fillna(0).astype(int)
    out.loc[out["effectiveAttempts"].eq(0), "effectiveAttempts"] = out.loc[
        out["effectiveAttempts"].eq(0), "attemptsFromReports"
    ]
    return out


@st.cache_data(ttl=120)
def load_events() -> List[Dict[str, Any]]:
    client = JamClient()
    try:
        payload = client.list_events_past()
        return payload.get("events", [])
    except Exception:
        return []


def run_sync(full: bool = False):
    """Synchronize in-process and reload the UI with the new database data."""
    from jam_mapper.core.sync import sync_challenges

    try:
        with st.spinner("Sincronizando dados com a AWS Jam..."):
            result = sync_challenges(full=full)
    except Exception as exc:
        st.error(
            "Falha na sincronização com a AWS Jam. O token configurado provavelmente não tem acesso a esta rota administrativa ou o ambiente está diferente do esperado."
        )
        st.caption(str(exc))
        return

    imported = int(result.get("imported") or 0)
    if imported == 0:
        st.warning("A AWS Jam respondeu, mas nenhum challenge foi importado. Verifique o token e a conta utilizada.")
        return

    st.cache_data.clear()
    st.session_state.sync_notice = f"Sincronização concluída: {imported} challenges importados."
    rerun = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if callable(rerun):
        rerun()
    st.success(st.session_state.sync_notice)


def sync_reports_from_ids(event_ids: List[str]):
    from jam_mapper.core.sync import sync_event_reports

    with st.spinner("Sincronizando reports de eventos..."):
        result = sync_event_reports(event_ids)
    st.cache_data.clear()
    if result["errors"]:
        st.warning(f"Reports importados: {result['imported']}. Erros: {len(result['errors'])}")
        st.json(result["errors"])
    else:
        st.success(f"Reports importados: {result['imported']}")


def recommend_challenges(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Recommend challenges using catalog difficulty plus personal progress."""
    if df is None or df.empty:
        return pd.DataFrame()

    df2 = df.copy()
    df2["numInputTasks"] = df2["numInputTasks"].fillna(0)
    df2["difficulty"] = df2["difficulty"].fillna(0)
    df2["avgSolveSeconds"] = df2["avgSolveSeconds"].fillna(0)

    status_series = df2["effectiveStatus"] if "effectiveStatus" in df2.columns else df2["status"]
    status_weight = status_series.map(
        {"review": 30, "in_progress": 20, "not_started": 10, "done": -50}
    ).fillna(0)
    personal_weight = df2["personalDifficulty"].fillna(0) * 6
    df2["score"] = (
        df2["numInputTasks"] * 3
        + df2["difficulty"] * 2
        + (df2["avgSolveSeconds"] / 60.0)
        + status_weight
        + personal_weight
    )
    return df2.sort_values(by="score", ascending=False).head(n)


def format_duration(minutes: int) -> str:
    minutes = int(minutes or 0)
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}min"
    if hours:
        return f"{hours}h"
    return f"{mins}min"
