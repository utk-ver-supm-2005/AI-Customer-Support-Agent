"""
ticket_tracker.py
Independent per-complaint lifecycle progress tracking and persistence.
Uses Python's standard sqlite3 library for reliable, lightweight persistence.

Lifecycle Stages:
- Received — 0%
- Analyzed — 25%
- Classified & Routed — 50%
- In Progress — 75%
- Resolved — 100%
"""

import os
import json
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Union

# Default DB Path in the current workspace directory
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets_tracker.db")


class TicketStage(str, Enum):
    RECEIVED = "Received"
    ANALYZED = "Analyzed"
    CLASSIFIED_ROUTED = "Classified & Routed"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


STAGE_PROGRESS: Dict[TicketStage, int] = {
    TicketStage.RECEIVED: 0,
    TicketStage.ANALYZED: 25,
    TicketStage.CLASSIFIED_ROUTED: 50,
    TicketStage.IN_PROGRESS: 75,
    TicketStage.RESOLVED: 100,
}

STAGE_ORDER: List[TicketStage] = [
    TicketStage.RECEIVED,
    TicketStage.ANALYZED,
    TicketStage.CLASSIFIED_ROUTED,
    TicketStage.IN_PROGRESS,
    TicketStage.RESOLVED,
]

STAGE_DESCRIPTIONS: Dict[TicketStage, str] = {
    TicketStage.RECEIVED: "Request ingested and registered in support system",
    TicketStage.ANALYZED: "Objective 1: NLP issue, intent & entities extracted",
    TicketStage.CLASSIFIED_ROUTED: "Objective 2: Support category & operational queue assigned",
    TicketStage.IN_PROGRESS: "Assigned team actively working on resolution",
    TicketStage.RESOLVED: "Resolution completed and verified",
}

STAGE_BADGE_CLASSES: Dict[TicketStage, str] = {
    TicketStage.RECEIVED: "stage-badge-received",
    TicketStage.ANALYZED: "stage-badge-analyzed",
    TicketStage.CLASSIFIED_ROUTED: "stage-badge-routed",
    TicketStage.IN_PROGRESS: "stage-badge-progress",
    TicketStage.RESOLVED: "stage-badge-resolved",
}


def normalize_stage(stage_val: Union[TicketStage, str]) -> TicketStage:
    """Normalize string or enum to TicketStage, defaulting to RECEIVED if unrecognized."""
    if isinstance(stage_val, TicketStage):
        return stage_val
    clean = str(stage_val).strip()
    for s in TicketStage:
        if s.value.lower() == clean.lower() or s.name.lower() == clean.lower():
            return s
    # Partial matching for common variants
    if "received" in clean.lower():
        return TicketStage.RECEIVED
    if "analyzed" in clean.lower():
        return TicketStage.ANALYZED
    if "routed" in clean.lower() or "classified" in clean.lower():
        return TicketStage.CLASSIFIED_ROUTED
    if "progress" in clean.lower():
        return TicketStage.IN_PROGRESS
    if "resolved" in clean.lower():
        return TicketStage.RESOLVED
    return TicketStage.RECEIVED


def get_stage_progress(stage: Union[TicketStage, str]) -> int:
    """Returns the integer progress percentage (0, 25, 50, 75, 100) for a stage."""
    norm = normalize_stage(stage)
    return STAGE_PROGRESS.get(norm, 0)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a connection with row factory enabled."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initializes the SQLite schema and seeds default demonstration tickets
    starting at 'Received' (0%) if not already populated.
    """
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                scenario_key TEXT UNIQUE,
                stage TEXT NOT NULL,
                progress INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                history TEXT NOT NULL
            );
            """)

            # Seed the 6 demonstration scenarios if table is currently empty
            cursor = conn.execute("SELECT COUNT(*) as count FROM tickets")
            count = cursor.fetchone()["count"]

            if count == 0:
                from sample_scenarios import SCENARIOS
                now_iso = datetime.now(timezone.utc).isoformat()
                for key, sc in SCENARIOS.items():
                    t_id = sc.get("ticket_id", key)
                    init_history = json.dumps([{
                        "stage": TicketStage.RECEIVED.value,
                        "progress": 0,
                        "timestamp": now_iso,
                        "note": "Initial ticket intake"
                    }])
                    conn.execute("""
                    INSERT OR IGNORE INTO tickets (ticket_id, scenario_key, stage, progress, updated_at, history)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (t_id, key, TicketStage.RECEIVED.value, 0, now_iso, init_history))

                # Seed custom intake entry
                custom_history = json.dumps([{
                    "stage": TicketStage.RECEIVED.value,
                    "progress": 0,
                    "timestamp": now_iso,
                    "note": "Custom intake slot ready"
                }])
                conn.execute("""
                INSERT OR IGNORE INTO tickets (ticket_id, scenario_key, stage, progress, updated_at, history)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "#CUSTOM-LIVE",
                    "📝 Custom Request (Paste Any Message)",
                    TicketStage.RECEIVED.value,
                    0,
                    now_iso,
                    custom_history
                ))
    finally:
        conn.close()


def get_ticket(ticket_identifier: str, db_path: Optional[str] = None) -> dict:
    """
    Retrieve ticket status by ticket_id (e.g. '#TECH-401') or scenario_key.
    If the ticket does not exist, it is automatically initialized to 'Received' (0%).
    """
    if not ticket_identifier:
        ticket_identifier = "#CUSTOM-LIVE"

    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("""
            SELECT ticket_id, scenario_key, stage, progress, updated_at, history
            FROM tickets
            WHERE ticket_id = ? OR scenario_key = ?
            LIMIT 1;
        """, (ticket_identifier, ticket_identifier))
        row = cursor.fetchone()

        if row:
            history_list = []
            try:
                history_list = json.loads(row["history"])
            except Exception:
                history_list = []

            return {
                "ticket_id": row["ticket_id"],
                "scenario_key": row["scenario_key"],
                "stage": row["stage"],
                "progress": int(row["progress"]),
                "updated_at": row["updated_at"],
                "history": history_list,
            }

        # Auto-initialize new / custom ticket as Received (0%)
        now_iso = datetime.now(timezone.utc).isoformat()
        t_id = ticket_identifier if ticket_identifier.startswith("#") else f"#{ticket_identifier}"
        init_history = json.dumps([{
            "stage": TicketStage.RECEIVED.value,
            "progress": 0,
            "timestamp": now_iso,
            "note": "New ticket intake created"
        }])

        with conn:
            conn.execute("""
            INSERT OR REPLACE INTO tickets (ticket_id, scenario_key, stage, progress, updated_at, history)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (t_id, ticket_identifier, TicketStage.RECEIVED.value, 0, now_iso, init_history))

        return {
            "ticket_id": t_id,
            "scenario_key": ticket_identifier,
            "stage": TicketStage.RECEIVED.value,
            "progress": 0,
            "updated_at": now_iso,
            "history": json.loads(init_history),
        }
    finally:
        conn.close()


def update_ticket_stage(
    ticket_identifier: str,
    new_stage: Union[TicketStage, str],
    note: str = "",
    db_path: Optional[str] = None
) -> dict:
    """
    Updates the stage of a ticket and commits changes immediately to SQLite.
    Returns the updated ticket dictionary.
    """
    init_db(db_path)
    stage_enum = normalize_stage(new_stage)
    progress_val = STAGE_PROGRESS[stage_enum]
    now_iso = datetime.now(timezone.utc).isoformat()

    current_data = get_ticket(ticket_identifier, db_path=db_path)
    history = current_data.get("history", [])
    history.append({
        "stage": stage_enum.value,
        "progress": progress_val,
        "timestamp": now_iso,
        "note": note or f"Transitioned to {stage_enum.value}"
    })

    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("""
            UPDATE tickets
            SET stage = ?, progress = ?, updated_at = ?, history = ?
            WHERE ticket_id = ? OR scenario_key = ?;
            """, (
                stage_enum.value,
                progress_val,
                now_iso,
                json.dumps(history),
                current_data["ticket_id"],
                current_data["scenario_key"],
            ))
    finally:
        conn.close()

    return get_ticket(current_data["ticket_id"], db_path=db_path)


def get_all_tickets(db_path: Optional[str] = None) -> List[dict]:
    """Retrieve all tickets from SQLite database."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("""
            SELECT ticket_id, scenario_key, stage, progress, updated_at, history
            FROM tickets
            ORDER BY ticket_id ASC;
        """)
        rows = cursor.fetchall()
        results = []
        for r in rows:
            try:
                hist = json.loads(r["history"])
            except Exception:
                hist = []
            results.append({
                "ticket_id": r["ticket_id"],
                "scenario_key": r["scenario_key"],
                "stage": r["stage"],
                "progress": int(r["progress"]),
                "updated_at": r["updated_at"],
                "history": hist,
            })
        return results
    finally:
        conn.close()


def reset_ticket(ticket_identifier: str, db_path: Optional[str] = None) -> dict:
    """Reset a single ticket back to Received (0%)."""
    return update_ticket_stage(ticket_identifier, TicketStage.RECEIVED, note="Manual demo reset", db_path=db_path)


def reset_all_tickets(db_path: Optional[str] = None) -> None:
    """Reset all tickets in the database back to Received (0%)."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        with conn:
            tickets = conn.execute("SELECT ticket_id, scenario_key FROM tickets").fetchall()
            for t in tickets:
                hist = json.dumps([{
                    "stage": TicketStage.RECEIVED.value,
                    "progress": 0,
                    "timestamp": now_iso,
                    "note": "Full demo state reset"
                }])
                conn.execute("""
                    UPDATE tickets
                    SET stage = ?, progress = ?, updated_at = ?, history = ?
                    WHERE ticket_id = ?;
                """, (TicketStage.RECEIVED.value, 0, now_iso, hist, t["ticket_id"]))
    finally:
        conn.close()

