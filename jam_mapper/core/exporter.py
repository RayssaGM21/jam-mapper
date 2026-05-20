import os
import pandas as pd
from jam_mapper.core.config import get_settings


def export_to_xlsx(challenges: list[dict], path: str | None = None) -> str:
    s = get_settings()
    out_dir = path or s.export_path
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for c in challenges:
        row = {
            "challengeId": c.get("challengeId"),
            "title": c.get("title"),
            "category": c.get("category"),
            "difficulty": c.get("difficulty"),
            "tags": ",".join(c.get("tags") or []) if c.get("tags") else None,
            "awsServices": ",".join(c.get("awsServices") or []) if c.get("awsServices") else None,
            "numTasks": c.get("numTasks"),
            "numInputTasks": c.get("numInputTasks"),
            "numLambdaTasks": c.get("numLambdaTasks"),
            "numAiTasks": c.get("numAiTasks"),
            "validationKinds": ",".join(c.get("validationKinds") or []),
            "hasInputAnswer": c.get("hasInputAnswer"),
            "hasLambdaValidation": c.get("hasLambdaValidation"),
            "hasAiValidation": c.get("hasAiValidation"),
            "avgSolveSeconds": c.get("avgSolveSeconds"),
            "passRate": c.get("passRate"),
            "difficultyRating": c.get("difficultyRating"),
            "rating": c.get("rating"),
            "totalIncorrect": c.get("totalIncorrect"),
            "totalRequestedClues": c.get("totalRequestedClues"),
            "stability": c.get("stability"),
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    out_file = os.path.join(out_dir, "challenges.xlsx")
    df.to_excel(out_file, index=False)
    try:
        import logging

        logger = logging.getLogger("jam_mapper.exporter")
        logger.info("Exported %d rows to %s", len(df), out_file)
    except Exception:
        pass
    return out_file
