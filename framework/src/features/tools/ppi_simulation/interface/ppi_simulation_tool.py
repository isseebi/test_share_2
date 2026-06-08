from typing import Dict, Any
from src.features.agent_brain.application.brain_loop import AgentTool
from src.features.tools.ppi_simulation.application.ppi_simulation_use_case import ExecutePPISimulationUseCase

class PPISimulationAgentTool(AgentTool):
    def __init__(self, use_case: ExecutePPISimulationUseCase):
        self.use_case = use_case

    @property
    def name(self) -> str:
        return "ppi_simulation_tool"

    @property
    def description(self) -> str:
        return "Run a discrete-time physical numerical simulation of a DC motor with a cascaded P-PI controller (proportional outer loop, proportional-integral inner loop) to evaluate position response, errors, steady state error, and overshoot percentage."

    @property
    def args_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "kp": {
                    "type": "number",
                    "description": "Proportional gain of the outer position loop (Kp)"
                },
                "kvp": {
                    "type": "number",
                    "description": "Proportional gain of the inner velocity loop (Kvp)"
                },
                "kvi": {
                    "type": "number",
                    "description": "Integral gain of the inner velocity loop (Kvi)"
                },
                "steps": {
                    "type": "integer",
                    "description": "Number of simulation steps (default: 50)"
                }
            },
            "required": ["kp", "kvp", "kvi"]
        }

    def execute(self, args: Dict[str, Any]) -> str:
        kp = float(args.get("kp", 1.0))
        kvp = float(args.get("kvp", 1.0))
        kvi = float(args.get("kvi", 0.0))
        steps = int(args.get("steps", 50))
        return self.use_case.execute(kp=kp, kvp=kvp, kvi=kvi, steps=steps)
