"""
Interview Tracker Service & Database Module

Manages interview scheduling, status tracking, and timeline management for applications.
"""

import sqlite3
from typing import List, Dict, Optional, Tuple, Any

DB_NAME = 'job_tracker.db'

ALLOWED_ROUNDS = ['Screening', 'Technical', 'Coding', 'Managerial', 'HR', 'Final']
ALLOWED_TYPES = ['Online', 'Phone', 'In-person']
ALLOWED_STATUSES = ['Scheduled', 'Completed', 'Passed', 'Failed', 'Pending']

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def create_interviews_table():
    """Create the interviews table related to applications via application_id."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            interview_date TEXT NOT NULL,
            interview_round TEXT NOT NULL,
            interview_type TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def validate_interview_payload(data: dict) -> Tuple[bool, Optional[str], dict]:
    """
    Validate interview input fields.
    Returns: (is_valid, error_message, cleaned_dict)
    """
    if not isinstance(data, dict):
        return False, 'Invalid payload format; JSON object expected.', {}

    raw_date = str(data.get('interview_date', '')).strip()
    raw_round = str(data.get('interview_round', '')).strip()
    raw_type = str(data.get('interview_type', 'Online')).strip()
    raw_status = str(data.get('status', 'Scheduled')).strip()
    raw_notes = str(data.get('notes', '')).strip()

    if not raw_date:
        return False, 'Interview date is required.', {}

    if not raw_round:
        return False, 'Interview round is required.', {}

    # Case-insensitive normalization for round
    matched_round = next((r for r in ALLOWED_ROUNDS if r.lower() == raw_round.lower()), None)
    if not matched_round:
        return False, f"Invalid interview round '{raw_round}'. Allowed: {', '.join(ALLOWED_ROUNDS)}.", {}

    # Normalization for type
    matched_type = next((t for t in ALLOWED_TYPES if t.lower() == raw_type.lower()), None)
    if not matched_type:
        return False, f"Invalid interview type '{raw_type}'. Allowed: {', '.join(ALLOWED_TYPES)}.", {}

    # Normalization for status
    matched_status = next((s for s in ALLOWED_STATUSES if s.lower() == raw_status.lower()), None)
    if not matched_status:
        return False, f"Invalid status '{raw_status}'. Allowed: {', '.join(ALLOWED_STATUSES)}.", {}

    cleaned = {
        'interview_date': raw_date,
        'interview_round': matched_round,
        'interview_type': matched_type,
        'status': matched_status,
        'notes': raw_notes
    }
    return True, None, cleaned

def get_interviews_by_application_id(application_id: int) -> List[Dict[str, Any]]:
    """Retrieve all interviews for a specific application ordered by interview_date ASC, id ASC."""
    conn = get_db_connection()
    rows = conn.execute(
        '''
        SELECT i.*, a.company, a.job_role
        FROM interviews i
        JOIN applications a ON i.application_id = a.id
        WHERE i.application_id = ?
        ORDER BY i.interview_date ASC, i.id ASC
        ''',
        (application_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_interview_by_id(interview_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single interview record by its primary key ID."""
    conn = get_db_connection()
    row = conn.execute(
        '''
        SELECT i.*, a.company, a.job_role
        FROM interviews i
        JOIN applications a ON i.application_id = a.id
        WHERE i.id = ?
        ''',
        (interview_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def create_interview(application_id: int, interview_date: str, interview_round: str,
                     interview_type: str, status: str, notes: str = '') -> Optional[Dict[str, Any]]:
    """Insert a new interview record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO interviews (
            application_id, interview_date, interview_round, interview_type, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''',
        (application_id, interview_date, interview_round, interview_type, status, notes)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_interview_by_id(new_id)

def update_interview(interview_id: int, interview_date: str, interview_round: str,
                     interview_type: str, status: str, notes: str = '') -> Optional[Dict[str, Any]]:
    """Update an existing interview record."""
    conn = get_db_connection()
    conn.execute(
        '''
        UPDATE interviews
        SET interview_date = ?, interview_round = ?, interview_type = ?, status = ?, notes = ?
        WHERE id = ?
        ''',
        (interview_date, interview_round, interview_type, status, notes, interview_id)
    )
    conn.commit()
    conn.close()
    return get_interview_by_id(interview_id)

def delete_interview(interview_id: int) -> bool:
    """Delete an interview record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM interviews WHERE id = ?', (interview_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
