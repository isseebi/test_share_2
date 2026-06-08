from typing import List, Dict, Any, Tuple
from src.features.chat.application.use_cases import AgentBrainService
from src.features.chat.domain.entities import Message
from src.features.agent_brain.application.brain_loop import AgentThinkingLoop

class AgentBrainAdapter(AgentBrainService):
    def __init__(self, thinking_loop: AgentThinkingLoop):
        self.thinking_loop = thinking_loop

    def think_and_respond(
        self,
        conversation_history: List[Message],
        new_message: Message
    ) -> Tuple[str, List[Dict[str, Any]]]:
        # 1. Format inputs for LangGraphAgentState
        messages_state = []
        for msg in conversation_history:
            messages_state.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add the new user message
        messages_state.append({
            "role": new_message.role,
            "content": new_message.content
        })

        # 2. Run the LangGraph agent loop
        result = self.thinking_loop.run(messages_state)

        # 3. Extract output response content and thinking steps
        response_content = result.get("response") or "I encountered an error generating a response."
        thinking_steps = result.get("thinking_steps") or []

        return response_content, thinking_steps
