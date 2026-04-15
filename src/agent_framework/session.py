"""
Session Manager - Session persistence and resume

Inspired by claw-code's session management:
- JSONL format for audit trail
- SQLite for efficient session queries
- Automatic session compaction
- Session metadata and usage tracking

Session Lifecycle:
    CREATED -> ACTIVE -> COMPACTED -> ENDED
                 ↓
              RESUMED
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SessionState(Enum):
    """Session lifecycle states"""
    CREATED = "created"
    ACTIVE = "active"
    COMPACTED = "compacted"
    ENDED = "ended"
    RESUMED = "resumed"


@dataclass
class Message:
    """A message in the session"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)


@dataclass
class Session:
    """
    Session definition with full history.

    Attributes:
        id: Unique session identifier
        state: Current session state
        created_at: Session creation time
        updated_at: Last update time
        ended_at: Session end time
        messages: List of conversation messages
        metadata: Session metadata (model, permission mode, etc.)
        usage: Token usage statistics
        working_dir: Working directory for this session
    """
    id: str
    state: SessionState = SessionState.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    messages: List[Message] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    usage: dict = field(default_factory=lambda: {
        "input_tokens": 0,
        "output_tokens": 0,
        "cost": 0.0
    })
    working_dir: str = "."

    def __post_init__(self):
        """Generate ID if not provided"""
        if not self.id:
            self.id = f"session_{uuid.uuid4().hex[:12]}"

    def add_message(self, role: str, content: str, metadata: dict = None) -> None:
        """Add a message to the session"""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata or {}
        ))
        self.updated_at = datetime.now()

    def compact(self) -> int:
        """
        Compact session by removing oldest messages.

        Keeps system prompt and last N messages.

        Returns:
            Number of messages removed
        """
        # Keep system prompt and last 50 messages
        system_messages = [m for m in self.messages if m.role == "system"]
        other_messages = [m for m in self.messages if m.role != "system"]

        kept = other_messages[-50:]
        removed = len(other_messages) - len(kept)

        self.messages = system_messages + kept
        self.state = SessionState.COMPACTED
        self.updated_at = datetime.now()

        return removed

    def to_dict(self) -> dict:
        """Serialize session to dictionary"""
        return {
            "id": self.id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "metadata": m.metadata
                }
                for m in self.messages
            ],
            "metadata": self.metadata,
            "usage": self.usage,
            "working_dir": self.working_dir
        }


class SessionManager:
    """
    Session persistence manager.

    Features:
    - JSONL storage for full audit trail
    - SQLite for efficient session queries
    - Thread-safe operations
    - Automatic compaction
    - Session resume across restarts

    Inspired by claw-code's session management:
    - Session persistence in ~/.claude/sessions/
    - JSONL format for each session
    - SQLite index for session queries
    """

    def __init__(
        self,
        session_dir: str = None,
        db_path: str = None
    ):
        """
        Initialize session manager.

        Args:
            session_dir: Directory for JSONL session files
            db_path: Path to SQLite database
        """
        self.session_dir = Path(session_dir or "~/.agent_framework/sessions").expanduser()
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path or str(self.session_dir / "sessions.db")
        self._lock = threading.RLock()
        self._logger = logging.getLogger("session_manager")

        # In-memory cache
        self._sessions: Dict[str, Session] = {}

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    ended_at TEXT,
                    metadata TEXT,
                    working_dir TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_updated
                ON sessions(updated_at DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_state
                ON sessions(state)
            """)
            conn.commit()

    def create_session(
        self,
        model: str = None,
        permission_mode: str = None,
        working_dir: str = "."
    ) -> Session:
        """
        Create a new session.

        Args:
            model: Model name
            permission_mode: Permission mode
            working_dir: Working directory

        Returns:
            Created Session instance
        """
        with self._lock:
            session = Session(
                id=f"session_{uuid.uuid4().hex[:12]}",
                metadata={
                    "model": model,
                    "permission_mode": permission_mode
                },
                working_dir=working_dir
            )
            session.state = SessionState.ACTIVE

            self._sessions[session.id] = session
            self._save_to_db(session)
            self._save_to_jsonl(session)

            self._logger.info(f"Created session: {session.id}")
            return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        with self._lock:
            # Check cache first
            if session_id in self._sessions:
                return self._sessions[session_id]

            # Load from database
            return self._load_from_db(session_id)

    def get_latest_session(self) -> Optional[Session]:
        """
        Get the most recent session.

        Returns:
            Most recent Session or None
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("""
                    SELECT id FROM sessions
                    ORDER BY updated_at DESC
                    LIMIT 1
                """).fetchone()

                if row:
                    return self.get_session(row[0])

            return None

    def list_sessions(
        self,
        state: SessionState = None,
        limit: int = 10
    ) -> List[Session]:
        """
        List sessions with optional filter.

        Args:
            state: Filter by state
            limit: Maximum sessions to return

        Returns:
            List of sessions
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                if state:
                    rows = conn.execute("""
                        SELECT id FROM sessions
                        WHERE state = ?
                        ORDER BY updated_at DESC
                        LIMIT ?
                    """, (state.value, limit)).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT id FROM sessions
                        ORDER BY updated_at DESC
                        LIMIT ?
                    """, (limit,)).fetchall()

                return [self.get_session(row[0]) for row in rows]

    def update_session(self, session: Session) -> None:
        """
        Update session (save to storage).

        Args:
            session: Session to save
        """
        with self._lock:
            session.updated_at = datetime.now()
            self._sessions[session.id] = session
            self._save_to_db(session)
            self._save_to_jsonl(session)

    def end_session(self, session_id: str) -> bool:
        """
        End a session.

        Args:
            session_id: Session to end

        Returns:
            True if session was ended
        """
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return False

            session.state = SessionState.ENDED
            session.ended_at = datetime.now()
            self.update_session(session)

            self._logger.info(f"Ended session: {session_id}")
            return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session to delete

        Returns:
            True if session was deleted
        """
        with self._lock:
            session = self._sessions.pop(session_id, None)

            if session:
                # Remove from database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                    conn.commit()

                # Remove JSONL file
                jsonl_path = self.session_dir / f"{session_id}.jsonl"
                if jsonl_path.exists():
                    jsonl_path.unlink()

                return True

            return False

    def compact_session(self, session_id: str) -> int:
        """
        Compact a session.

        Args:
            session_id: Session to compact

        Returns:
            Number of messages removed
        """
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return 0

            removed = session.compact()
            self.update_session(session)

            self._logger.info(f"Compacted session {session_id}: removed {removed} messages")
            return removed

    def resume_session(self, session_id: str) -> Optional[Session]:
        """
        Resume a session for continued interaction.

        Args:
            session_id: Session to resume

        Returns:
            Resumed Session or None
        """
        with self._lock:
            session = self.get_session(session_id)
            if not session:
                return None

            session.state = SessionState.RESUMED
            self.update_session(session)

            return session

    def _save_to_db(self, session: Session) -> None:
        """Save session to SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions
                (id, state, created_at, updated_at, ended_at, metadata, working_dir)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                session.state.value,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.ended_at.isoformat() if session.ended_at else None,
                json.dumps(session.metadata),
                session.working_dir
            ))
            conn.commit()

    def _load_from_db(self, session_id: str) -> Optional[Session]:
        """Load session from SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT * FROM sessions WHERE id = ?
            """, (session_id,)).fetchone()

            if not row:
                return None

            columns = [desc[0] for desc in conn.execute("SELECT * FROM sessions").description]
            data = dict(zip(columns, row))

            # Load messages from JSONL
            jsonl_path = self.session_dir / f"{session_id}.jsonl"
            messages = []

            if jsonl_path.exists():
                with open(jsonl_path) as f:
                    for line in f:
                        if line.strip():
                            msg = json.loads(line)
                            messages.append(Message(**msg))

            session = Session(
                id=data["id"],
                state=SessionState(data["state"]),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                ended_at=datetime.fromisoformat(data["ended_at"]) if data["ended_at"] else None,
                messages=messages,
                metadata=json.loads(data["metadata"]) if data["metadata"] else {},
                working_dir=data["working_dir"] or "."
            )

            self._sessions[session_id] = session
            return session

    def _save_to_jsonl(self, session: Session) -> None:
        """Append session to JSONL file"""
        jsonl_path = self.session_dir / f"{session.id}.jsonl"

        with open(jsonl_path, "a") as f:
            for msg in session.messages[-1:]:  # Only write new messages
                f.write(json.dumps(msg.__dict__) + "\n")

    def get_stats(self) -> dict:
        """Get session statistics"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
                active = conn.execute(
                    "SELECT COUNT(*) FROM sessions WHERE state = ?",
                    (SessionState.ACTIVE.value,)
                ).fetchone()[0]
                ended = conn.execute(
                    "SELECT COUNT(*) FROM sessions WHERE state = ?",
                    (SessionState.ENDED.value,)
                ).fetchone()[0]

                return {
                    "total": total,
                    "active": active,
                    "ended": ended
                }
