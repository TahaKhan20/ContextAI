from pathlib import Path
import json
import shutil
from datetime import datetime


SESSION_DIR = Path("sessions")

SESSION_DIR.mkdir(
    exist_ok=True
)


class SessionManager:


    def __init__(self):

        self.sessions = SESSION_DIR / "sessions.json"

        if not self.sessions.exists():

            self._save({})


    # --------------------------
    # Internal helpers
    # --------------------------

    def _load(self):

        with open(
            self.sessions,
            "r"
        ) as f:

            return json.load(f)



    def _save(self, data):

        with open(
            self.sessions,
            "w"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )


    # --------------------------
    # Create Session
    # --------------------------

    def create_session(self):

        import uuid

        session_id = str(
            uuid.uuid4()
        )


        data = self._load()


        data[session_id] = {

            "created":
                datetime.now().isoformat(),

            "title":
                "New Chat",

            "messages":[]

        }


        self._save(data)


        return session_id



    # --------------------------
    # List Sessions
    # --------------------------

    def list_sessions(self):

        data = self._load()

        sessions = []

        for sid, info in data.items():

            sessions.append({

                "id": sid,
                "title": info["title"],
                "created": info["created"],
                "messages": info.get("messages", [])

            })

        return sorted(
            sessions,
            key=lambda x: x["created"],
            reverse=True
        )

    # --------------------------
    # Loading Session
    # --------------------------

    def load_session(self, session_id):

        data = self._load()

        if session_id not in data:
            return None

        return {

            "id": session_id,
            "title": data[session_id]["title"],
            "messages": data[session_id]["messages"]

        }

    # --------------------------
    # Delete Session
    # --------------------------

    def delete_session(
        self,
        session_id
    ):


        data=self._load()


        if session_id in data:

            del data[session_id]


            self._save(data)



        # remove uploaded files

        upload_dir = Path(
            "uploads"
        ) / session_id


        if upload_dir.exists():

            shutil.rmtree(
                upload_dir
            )


        # remove vector index

        storage_dir = Path(
            "storage"
        ) / session_id


        if storage_dir.exists():

            shutil.rmtree(
                storage_dir
            )



        return True

    # --------------------------
    # Rename Session
    # --------------------------

    def rename_session(self, session_id: str, title: str):

        data = self._load()

        if session_id not in data:
            return None

        data[session_id]["title"] = title.strip()

        self._save(data)

        return {
            "id": session_id,
            "title": title
        }

    # --------------------------
    # Save Chat Message
    # --------------------------

    def add_message(
        self,
        session_id,
        role,
        content
    ):


        data=self._load()


        if session_id not in data:
            return



        data[session_id]["messages"].append({

            "role":role,

            "content":content,

            "time":
                datetime.now().isoformat()

        })


        # auto title

        if (
            data[session_id]["title"]
            ==
            "New Chat"
        ):

            words = content.split()

            data[session_id]["title"] = (
                " ".join(words[:5])
            )



        self._save(data)



    # --------------------------
    # Get Chat History
    # --------------------------

    def get_history(
        self,
        session_id
    ):


        data=self._load()


        if session_id not in data:

            return []


        return data[session_id]["messages"]