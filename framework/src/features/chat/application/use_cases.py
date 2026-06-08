from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.features.chat.domain.entities import ChatSession, Message
from src.shared.domain.value_objects import SessionId

# DTOs
class SendMessageInputDTO:
    def __init__(self, content: str, session_id: Optional[str] = None):
        self.content = content
        self.session_id = session_id


class SendMessageOutputDTO:
    def __init__(self, session_id: str, response_content: str, thinking_steps: List[Dict[str, Any]], messages: List[Dict[str, Any]]):
        self.session_id = session_id
        self.response_content = response_content
        self.thinking_steps = thinking_steps
        self.messages = messages

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "response_content": self.response_content,
            "thinking_steps": self.thinking_steps,
            "messages": self.messages
        }


# Interfaces / Ports
class ChatSessionRepository(ABC):
    @abstractmethod
    def save(self, session: ChatSession) -> None:
        pass

    @abstractmethod
    def find_by_id(self, session_id: SessionId) -> Optional[ChatSession]:
        pass

    @abstractmethod
    def list_all(self) -> List[ChatSession]:
        pass


class AgentBrainService(ABC):
    @abstractmethod
    def think_and_respond(self, conversation_history: List[Message], new_message: Message) -> tuple[str, List[Dict[str, Any]]]:
        """
        Processes history + message, returns (response_content, thinking_steps).
        """
        pass


# Concrete Use Cases
class SendMessageUseCase:
    def __init__(self, repository: ChatSessionRepository, agent_brain: AgentBrainService):
        self.repository = repository
        self.agent_brain = agent_brain

    def execute(self, input_dto: SendMessageInputDTO) -> SendMessageOutputDTO:
        # 1. Resolve Session
        if input_dto.session_id:
            s_id = SessionId(input_dto.session_id)
            session = self.repository.find_by_id(s_id)
            if not session:
                session = ChatSession(session_id=s_id)
        else:
            session = ChatSession()

        # 2. Add user message
        user_msg = Message(role="user", content=input_dto.content)
        session.add_message(user_msg)

        # 3. Call Agent Brain
        # Pass copy of history to avoid mutating inside the brain until we are ready
        history = list(session.messages[:-1])
        response_content, thinking_steps = self.agent_brain.think_and_respond(history, user_msg)

        # 4. Add assistant message
        assistant_msg = Message(role="assistant", content=response_content)
        session.add_message(assistant_msg)

        # 5. Persist Session
        self.repository.save(session)

        # 6. Return response
        return SendMessageOutputDTO(
            session_id=str(session.session_id),
            response_content=response_content,
            thinking_steps=thinking_steps,
            messages=[msg.to_dict() for msg in session.messages]
        )


class GetSessionsUseCase:
    def __init__(self, repository: ChatSessionRepository):
        self.repository = repository

    def execute(self) -> List[Dict[str, Any]]:
        sessions = self.repository.list_all()
        # Return sorted by ID or date, let's just return mapped DTOs
        return [
            {
                "session_id": str(s.session_id),
                "last_message": s.messages[-1].content if s.messages else "New Session"
            }
            for s in sessions
        ]
