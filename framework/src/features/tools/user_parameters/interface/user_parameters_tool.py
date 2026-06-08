from typing import Dict, Any
from src.features.agent_brain.application.brain_loop import AgentTool
from src.features.tools.user_parameters.application.user_parameters_use_case import GetUserParametersUseCase

class UserParametersAgentTool(AgentTool):
    def __init__(self, use_case: GetUserParametersUseCase):
        self.use_case = use_case

    @property
    def name(self) -> str:
        return "user_parameters_tool"

    @property
    def description(self) -> str:
        return "Retrieve the current user/system-specific PPI controller parameters (Kp, Kvp, Kvi) and configuration notes in a JSON format with natural language explanations."

    @property
    def args_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {}
        }

    def execute(self, args: Dict[str, Any]) -> str:
        return self.use_case.execute()
