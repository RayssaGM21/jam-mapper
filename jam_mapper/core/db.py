import sqlite3
import json
from typing import Dict, Any, Optional, List
from jam_mapper.core.config import get_settings


class Database:
    def __init__(self, path: Optional[str] = None):
        s = get_settings()
        self.path = path or s.sqlite_path
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS challenges (
                challengeId TEXT PRIMARY KEY,
                data TEXT,
                title TEXT,
                category TEXT,
                difficulty INTEGER,
                tags TEXT,
                awsServices TEXT,
                jamType TEXT,
                numTasks INTEGER,
                numInputTasks INTEGER,
                numLambdaTasks INTEGER DEFAULT 0,
                numAiTasks INTEGER DEFAULT 0,
                validationKinds TEXT,
                hasInputAnswer INTEGER DEFAULT 0,
                hasLambdaValidation INTEGER DEFAULT 0,
                hasAiValidation INTEGER DEFAULT 0,
                avgSolveSeconds INTEGER,
                rating REAL,
                difficultyRating REAL,
                passRate REAL,
                totalIncorrect INTEGER,
                totalRequestedClues INTEGER,
                totalCorrect INTEGER,
                stability REAL,
                lastSynced INTEGER
            )
            """
        )
        self._ensure_columns(
            "challenges",
            {
                "numLambdaTasks": "INTEGER DEFAULT 0",
                "numAiTasks": "INTEGER DEFAULT 0",
                "validationKinds": "TEXT",
                "hasInputAnswer": "INTEGER DEFAULT 0",
                "hasLambdaValidation": "INTEGER DEFAULT 0",
                "hasAiValidation": "INTEGER DEFAULT 0",
                "rating": "REAL",
                "difficultyRating": "REAL",
                "passRate": "REAL",
                "totalIncorrect": "INTEGER",
                "totalRequestedClues": "INTEGER",
                "totalCorrect": "INTEGER",
                "stability": "REAL",
            },
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                eventId TEXT PRIMARY KEY,
                data TEXT,
                title TEXT,
                startTime TEXT,
                endTime TEXT,
                totalChallenges INTEGER,
                solvedChallenges INTEGER,
                lastSynced INTEGER
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS event_reports (
                eventId TEXT PRIMARY KEY,
                data TEXT,
                lastSynced INTEGER
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jam_progress (
                challengeId TEXT PRIMARY KEY,
                status TEXT DEFAULT 'not_started',
                personalDifficulty INTEGER DEFAULT 0,
                timeSpentMinutes INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 0,
                lastPracticedAt TEXT,
                targetReviewAt TEXT,
                blockers TEXT,
                notes TEXT,
                solutionMarkdownPath TEXT,
                updatedAt INTEGER
            )
            """
        )
        self._ensure_columns("jam_progress", {"solutionMarkdownPath": "TEXT"})
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updatedAt INTEGER
            )
            """
        )
        self._conn.commit()

    def _ensure_columns(self, table: str, columns: Dict[str, str]):
        cur = self._conn.cursor()
        existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, definition in columns.items():
            if name not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    def upsert_challenge(self, challenge_id: str, full_data: Dict[str, Any], last_synced: Optional[int] = None):
        cur = self._conn.cursor()
        title = full_data.get("title")
        category = full_data.get("category")
        difficulty = full_data.get("difficulty")
        tags = json.dumps(full_data.get("tags")) if full_data.get("tags") is not None else None
        aws = json.dumps(full_data.get("awsServices")) if full_data.get("awsServices") is not None else None
        jamtype = full_data.get("jamType")
        num_tasks = int(full_data.get("numTasks") or 0)
        num_input = int(full_data.get("numInputTasks") or 0)
        num_lambda = int(full_data.get("numLambdaTasks") or 0)
        num_ai = int(full_data.get("numAiTasks") or 0)
        validation_kinds = json.dumps(full_data.get("validationKinds") or [])
        avg = full_data.get("avgSolveSeconds")
        cur.execute(
            """
            REPLACE INTO challenges (
                challengeId, data, title, category, difficulty, tags, awsServices, jamType,
                numTasks, numInputTasks, numLambdaTasks, numAiTasks, validationKinds,
                hasInputAnswer, hasLambdaValidation, hasAiValidation, avgSolveSeconds,
                rating, difficultyRating, passRate, totalIncorrect, totalRequestedClues,
                totalCorrect, stability, lastSynced
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                challenge_id,
                json.dumps(full_data),
                title,
                category,
                difficulty,
                tags,
                aws,
                jamtype,
                num_tasks,
                num_input,
                num_lambda,
                num_ai,
                validation_kinds,
                int(bool(full_data.get("hasInputAnswer"))),
                int(bool(full_data.get("hasLambdaValidation"))),
                int(bool(full_data.get("hasAiValidation"))),
                avg,
                full_data.get("rating"),
                full_data.get("difficultyRating"),
                full_data.get("passRate"),
                full_data.get("totalIncorrect"),
                full_data.get("totalRequestedClues"),
                full_data.get("totalCorrect"),
                full_data.get("stability"),
                last_synced,
            ),
        )
        self._conn.commit()
        try:
            import logging

            logger = logging.getLogger("jam_mapper.db")
            logger.debug("Upserted challenge %s (title=%s)", challenge_id, title)
        except Exception:
            pass

    def list_challenges(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT data FROM challenges")
        rows = cur.fetchall()
        out = []
        for (d,) in rows:
            try:
                out.append(json.loads(d))
            except Exception:
                out.append({})
        return out

    def upsert_event(self, event_id: str, full_data: Dict[str, Any], last_synced: Optional[int] = None):
        cur = self._conn.cursor()
        title = full_data.get("title")
        start = full_data.get("startTime")
        end = full_data.get("endTime")
        prog = full_data.get("progress") or {}
        total = int(prog.get("totalChallenges") or 0)
        solved = int(prog.get("solvedChallenges") or 0)
        cur.execute(
            "REPLACE INTO events (eventId, data, title, startTime, endTime, totalChallenges, solvedChallenges, lastSynced) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, json.dumps(full_data), title, start, end, total, solved, last_synced),
        )
        self._conn.commit()

    def upsert_event_report(self, event_id: str, report_data: Dict[str, Any], last_synced: Optional[int] = None):
        cur = self._conn.cursor()
        cur.execute(
            "REPLACE INTO event_reports (eventId, data, lastSynced) VALUES (?, ?, ?)",
            (event_id, json.dumps(report_data), last_synced),
        )
        self._conn.commit()

    def list_events(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT data FROM events")
        rows = cur.fetchall()
        out = []
        for (d,) in rows:
            try:
                out.append(json.loads(d))
            except Exception:
                out.append({})
        return out

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT data FROM events WHERE eventId = ?", (event_id,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

    def list_event_reports(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT data FROM event_reports")
        rows = cur.fetchall()
        out = []
        for (d,) in rows:
            try:
                out.append(json.loads(d))
            except Exception:
                out.append({})
        return out

    def get_event_report(self, event_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT data FROM event_reports WHERE eventId = ?", (event_id,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

    def get_challenge(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT data FROM challenges WHERE challengeId = ?", (challenge_id,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None

    def list_progress(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT challengeId, status, personalDifficulty, timeSpentMinutes, attempts,
                   lastPracticedAt, targetReviewAt, blockers, notes, solutionMarkdownPath, updatedAt
            FROM jam_progress
            """
        )
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_progress(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT challengeId, status, personalDifficulty, timeSpentMinutes, attempts,
                   lastPracticedAt, targetReviewAt, blockers, notes, solutionMarkdownPath, updatedAt
            FROM jam_progress
            WHERE challengeId = ?
            """,
            (challenge_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, row))

    def upsert_progress(self, challenge_id: str, data: Dict[str, Any]):
        import time

        cur = self._conn.cursor()
        current = self.get_progress(challenge_id) or {}
        merged = {**current, **data}
        cur.execute(
            """
            REPLACE INTO jam_progress (
                challengeId, status, personalDifficulty, timeSpentMinutes, attempts,
                lastPracticedAt, targetReviewAt, blockers, notes, solutionMarkdownPath, updatedAt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                challenge_id,
                merged.get("status") or "not_started",
                int(merged.get("personalDifficulty") or 0),
                int(merged.get("timeSpentMinutes") or 0),
                int(merged.get("attempts") or 0),
                merged.get("lastPracticedAt"),
                merged.get("targetReviewAt"),
                merged.get("blockers"),
                merged.get("notes"),
                merged.get("solutionMarkdownPath"),
                int(time.time()),
            ),
        )
        self._conn.commit()

    def set_setting(self, key: str, value: Any):
        import time

        cur = self._conn.cursor()
        cur.execute(
            "REPLACE INTO app_settings (key, value, updatedAt) VALUES (?, ?, ?)",
            (key, json.dumps(value), int(time.time())),
        )
        self._conn.commit()

    def get_setting(self, key: str, default: Any = None) -> Any:
        cur = self._conn.cursor()
        cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            return default
        try:
            return json.loads(row[0])
        except Exception:
            return default
