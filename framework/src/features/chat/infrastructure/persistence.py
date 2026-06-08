import threading
from typing import Dict, List, Optional
from src.features.chat.domain.entities import ChatSession
from src.features.chat.application.use_cases import ChatSessionRepository
from src.shared.domain.value_objects import SessionId

class InMemoryChatSessionRepository(ChatSessionRepository):
    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}
        self._lock = threading.Lock()

    def save(self, session: ChatSession) -> None:
        with self._lock:
            self._sessions[str(session.session_id)] = session

    def find_by_id(self, session_id: SessionId) -> Optional[ChatSession]:
        with self._lock:
            return self._sessions.get(str(session_id))

    def list_all(self) -> List[ChatSession]:
        with self._lock:
            # Return copy of list
            return list(self._sessions.values())
