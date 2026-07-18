from pathlib import Path
from uuid import uuid4
from datetime import datetime
import json
import shutil


class SessionManager:

    def __init__(self):

        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)

        self.uploads_dir = Path("uploads")
        self.uploads_dir.mkdir(exist_ok=True)

        self.storage_dir = Path("storage")
        self.storage_dir.mkdir(exist_ok=True)

    # ==========================================================
    # Helpers
    # ==========================================================

    def _session_file(self, session_id: str):

        return self.sessions_dir / f"{session_id}.json"

    # ==========================================================
    # Create Session
    # ==========================================================

    def create_session(self):

        session_id = str(uuid4())

        (self.uploads_dir / session_id).mkdir(
            parents=True,
            exist_ok=True
        )

        (self.storage_dir / session_id).mkdir(
            parents=True,
            exist_ok=True
        )

        session = {

            "id": session_id,

            "title": "New Chat",

            "created_at": datetime.now().isoformat(),

            "updated_at": datetime.now().isoformat(),

            "messages": []

        }

        self.save_session(session)

        return session

    # ==========================================================
    # Save Session
    # ==========================================================

    def save_session(self, session: dict):

        session["updated_at"] = datetime.now().isoformat()

        with open(
            self._session_file(session["id"]),
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                session,
                f,
                indent=4,
                ensure_ascii=False
            )

    # ==========================================================
    # Load Session
    # ==========================================================

    def load_session(self, session_id: str):

        path = self._session_file(session_id)

        if not path.exists():
            return None

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    # ==========================================================
    # List Sessions
    # ==========================================================

    def list_sessions(self):

        sessions = []

        for file in self.sessions_dir.glob("*.json"):

            with open(
                file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

            sessions.append({

                "id": data["id"],

                "title": data["title"],

                "created_at": data["created_at"],

                "updated_at": data["updated_at"]

            })

        sessions.sort(

            key=lambda x: x["updated_at"],

            reverse=True

        )

        return sessions

    # ==========================================================
    # Delete Session
    # ==========================================================

    def delete_session(self, session_id: str):

        session_file = self._session_file(session_id)

        if session_file.exists():
            session_file.unlink()

        shutil.rmtree(

            self.uploads_dir / session_id,

            ignore_errors=True

        )

        shutil.rmtree(

            self.storage_dir / session_id,

            ignore_errors=True

        )

    # ==========================================================
    # Rename Session
    # ==========================================================

    def rename_session(

        self,

        session_id: str,

        title: str

    ):

        session = self.load_session(session_id)

        if session is None:
            return None

        session["title"] = title

        self.save_session(session)

        return session

    # ==========================================================
    # Add Message
    # ==========================================================

    def add_message(

        self,

        session_id: str,

        role: str,

        content: str

    ):

        session = self.load_session(session_id)

        if session is None:
            return None

        session["messages"].append({

            "role": role,

            "content": content

        })

        self.save_session(session)

        return session

    # ==========================================================
    # Get Messages
    # ==========================================================

    def get_messages(self, session_id: str):

        session = self.load_session(session_id)

        if session is None:
            return []

        return session["messages"]

    # ==========================================================
    # Latest Session
    # ==========================================================

    def latest_session(self):

        sessions = self.list_sessions()

        if len(sessions) == 0:
            return None

        return self.load_session(

            sessions[0]["id"]

        )