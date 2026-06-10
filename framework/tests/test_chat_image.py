import pytest
from src.features.chat.domain.entities import Message
from src.shared.domain.value_objects import Timestamp
from src.features.chat.application.use_cases import (
    SendMessageInputDTO,
    SendMessageUseCase,
    ChatSessionRepository
)
from src.features.chat.domain.entities import ChatSession
from src.shared.domain.value_objects import SessionId

def test_message_entity_image_support():
    # Test message with image
    msg = Message(role="user", content="", image="data:image/png;base64,abcdef")
    assert msg.role == "user"
    assert msg.content == ""
    assert msg.image == "data:image/png;base64,abcdef"

    # Test serialization
    data = msg.to_dict()
    assert data["role"] == "user"
    assert data["content"] == ""
    assert data["image"] == "data:image/png;base64,abcdef"

    # Test deserialization
    msg2 = Message.from_dict(data)
    assert msg2.role == "user"
    assert msg2.content == ""
    assert msg2.image == "data:image/png;base64,abcdef"

    # Test empty validation
    with pytest.raises(ValueError):
        Message(role="user", content="")

def test_send_message_use_case_image():
    # Mock Repository
    class InMemoryRepo(ChatSessionRepository):
        def __init__(self):
            self.sessions = {}
        def save(self, session):
            self.sessions[str(session.session_id)] = session
        def find_by_id(self, session_id):
            return self.sessions.get(str(session_id))
        def list_all(self):
            return list(self.sessions.values())

    # Mock Brain
    class MockBrain:
        def think_and_respond(self, history, new_message):
            assert new_message.image == "data:image/png;base64,dummy"
            return "Responding to image", [{"node": "think", "status": "success", "message": "saw image"}]

    repo = InMemoryRepo()
    brain = MockBrain()
    use_case = SendMessageUseCase(repo, brain)

    input_dto = SendMessageInputDTO(
        content="look at this",
        session_id=None,
        image="data:image/png;base64,dummy"
    )

    output = use_case.execute(input_dto)
    assert output.response_content == "Responding to image"
    assert output.thinking_steps[0]["message"] == "saw image"
    
    # Verify image was stored in session
    session = repo.find_by_id(SessionId(output.session_id))
    assert len(session.messages) == 2
    assert session.messages[0].image == "data:image/png;base64,dummy"
    assert session.messages[1].image is None
