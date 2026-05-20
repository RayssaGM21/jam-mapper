from fastapi import FastAPI, HTTPException

from jam_mapper.core.db import Database
from jam_mapper.core.solutions import ensure_solution_file
from jam_mapper.core.sync import sync_challenges, sync_event_reports

app = FastAPI(title="AWS Jam Performance Hub API")


@app.post("/sync/challenges")
def sync_all(full: bool = True):
    try:
        return sync_challenges(full=full)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/sync/events")
def sync_events(event_ids: list[str]):
    try:
        return sync_event_reports(event_ids)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/challenges")
def list_local():
    return Database().list_challenges()


@app.post("/challenges/{challenge_id}/solution")
def create_solution(challenge_id: str):
    try:
        path = ensure_solution_file(challenge_id)
        return {"challengeId": challenge_id, "path": str(path)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
