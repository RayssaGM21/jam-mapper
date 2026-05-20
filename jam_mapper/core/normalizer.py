"""Normalize AWS Jam API payloads into local analytics records."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _has_ai_validation(task: Dict[str, Any]) -> bool:
    validation_type = str(task.get("validationType") or "").lower()
    validation_runtime = str(task.get("validationFunctionRuntime") or "").lower()
    validation_name = str(task.get("validationFunction") or "").lower()
    joined = " ".join([validation_type, validation_runtime, validation_name])
    return any(token in joined for token in ["ai", "bedrock", "llm", "model"])


def classify_task_validation(task: Dict[str, Any]) -> str:
    """Return a compact correction type for a task."""
    validation_type = str(task.get("validationType") or "").upper()
    if task.get("allowInputAnswer"):
        return "input_answer"
    if _has_ai_validation(task):
        return "ai"
    if "LAMBDA" in validation_type or task.get("validatedByLambda"):
        return "lambda"
    if validation_type:
        return validation_type.lower()
    return "unknown"


def normalize_tasks(tasks: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for task in tasks or []:
        validation_kind = classify_task_validation(task)
        normalized.append(
            {
                "id": task.get("id"),
                "taskNumber": task.get("taskNumber"),
                "title": task.get("title"),
                "scorePercent": task.get("scorePercent"),
                "validationType": task.get("validationType"),
                "validationKind": validation_kind,
                "allowInputAnswer": bool(task.get("allowInputAnswer")),
                "validatedByLambda": bool(task.get("validatedByLambda")),
                "dependsOnTaskIds": _as_list(task.get("dependsOnTaskIds")),
            }
        )
    return normalized


def normalize_challenge(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a list or detail API challenge payload."""
    latest = payload.get("latest") or payload.get("latestApproved") or payload
    challenge_id = latest.get("challengeId")
    props = latest.get("props") or {}
    tasks = normalize_tasks(props.get("tasks") or [])
    global_stats = payload.get("globalStatistics") or {}
    solve_times = global_stats.get("solveTimes") or {}

    validation_kinds = sorted({task["validationKind"] for task in tasks if task.get("validationKind")})
    num_input = sum(1 for task in tasks if task.get("allowInputAnswer"))
    num_lambda = sum(1 for task in tasks if task.get("validationKind") == "lambda")
    num_ai = sum(1 for task in tasks if task.get("validationKind") == "ai")

    return {
        "challengeId": challenge_id,
        "title": props.get("title"),
        "category": props.get("category"),
        "description": props.get("description"),
        "difficulty": props.get("difficulty"),
        "tags": _as_list(props.get("tags")),
        "awsServices": _as_list(props.get("awsServices")),
        "jamType": props.get("jamType"),
        "mode": props.get("mode"),
        "regionAllowlist": _as_list(props.get("regionAllowlist")),
        "sshKeyPairRequired": bool(props.get("sshKeyPairRequired")),
        "defaultLabProvider": props.get("defaultLabProvider"),
        "learningOutcome": props.get("learningOutcome"),
        "nextSteps": props.get("nextSteps"),
        "tasks": tasks,
        "numTasks": len(tasks),
        "numInputTasks": num_input,
        "numLambdaTasks": num_lambda,
        "numAiTasks": num_ai,
        "validationKinds": validation_kinds,
        "hasInputAnswer": num_input > 0,
        "hasLambdaValidation": num_lambda > 0,
        "hasAiValidation": num_ai > 0,
        "avgSolveSeconds": solve_times.get("trimmedAvgSeconds"),
        "lowestSolveSeconds": (solve_times.get("lowestSolveTime") or {}).get("numSeconds"),
        "highestSolveSeconds": (solve_times.get("highestSolveTime") or {}).get("numSeconds"),
        "rating": global_stats.get("rating"),
        "ratingCount": global_stats.get("ratingCount"),
        "difficultyRating": global_stats.get("difficultyRating"),
        "jamsUsed": global_stats.get("jamsUsed"),
        "totalIncorrect": global_stats.get("totalIncorrect"),
        "totalRequestedClues": global_stats.get("totalRequestedClues"),
        "totalCorrect": global_stats.get("totalCorrect"),
        "passRate": global_stats.get("passRate"),
        "unresolvedChallengeIssues": global_stats.get("unresolvedChallengeIssues"),
        "highestIssueSeverity": global_stats.get("highestIssueSeverity"),
        "stability": latest.get("stability"),
        "statusAws": latest.get("status"),
        "version": latest.get("version"),
        "createdDate": latest.get("createdDate"),
        "isArchived": bool(payload.get("isArchived")),
        "isDefective": bool(payload.get("isDefective")),
        "isDemo": bool(payload.get("isDemo")),
        "isPublic": bool(payload.get("isPublic")),
    }
