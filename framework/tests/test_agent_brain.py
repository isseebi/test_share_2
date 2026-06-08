import pytest
from src.shared.infrastructure.config import Config
from src.features.agent_brain.infrastructure.llm_client import LLMClient
from src.features.agent_brain.application.brain_loop import AgentThinkingLoop
from src.features.tools.search.infrastructure.document_store import FileSystemDocumentStore
from src.features.tools.search.application.search_use_case import ExecuteSearchUseCase
from src.features.tools.search.interface.search_tool import SearchAgentTool
from src.features.tools.simulation.infrastructure.calculator import PhysicalPIDSimulator
from src.features.tools.simulation.application.simulation_use_case import ExecuteSimulationUseCase
from src.features.tools.simulation.interface.simulation_tool import SimulationAgentTool

def test_pid_simulation_math():
    """Verify that PID simulation executes and produces correct trajectory limits."""
    from src.features.tools.simulation.infrastructure.plot_generator import MatplotlibPlotGenerator
    simulator = PhysicalPIDSimulator()
    plot_generator = MatplotlibPlotGenerator()
    use_case = ExecuteSimulationUseCase(simulator, plot_generator)
    # Run a simple simulation
    result_text = use_case.execute(kp=2.0, ki=0.5, kd=0.1, steps=20)
    
    assert "PID Simulation completed" in result_text
    assert "STRUCTURED_DATA_JSON_START" in result_text
    
    # Verify values inside JSON
    import json
    json_part = result_text.split("STRUCTURED_DATA_JSON_START")[1].split("STRUCTURED_DATA_JSON_END")[0].strip()
    data = json.loads(json_part)
    
    assert "image" in data
    assert data["image"].startswith("data:image/png;base64,")
    assert "time" not in data
    assert "position" not in data
    assert data["metrics"]["max_value"] > 0


def test_agent_thinking_loop_search():
    """Verify that the LangGraph Agent Brain correctly triggers the search tool for search queries."""
    config = Config()
    # Force mock provider
    config.LLM_PROVIDER = "mock"
    
    from src.features.tools.simulation.infrastructure.plot_generator import MatplotlibPlotGenerator
    llm_client = LLMClient(config)
    doc_store = FileSystemDocumentStore(config)
    simulator = PhysicalPIDSimulator()
    plot_generator = MatplotlibPlotGenerator()
    
    search_use_case = ExecuteSearchUseCase(doc_store)
    sim_use_case = ExecuteSimulationUseCase(simulator, plot_generator)
    
    search_tool = SearchAgentTool(search_use_case)
    sim_tool = SimulationAgentTool(sim_use_case)
    
    thinking_loop = AgentThinkingLoop(llm_client, [search_tool, sim_tool])
    
    # Message prompting a search
    messages = [{"role": "user", "content": "Can you search for the XM-430 specifications?"}]
    result = thinking_loop.run(messages)
    
    assert result["response"] is not None
    steps = result["thinking_steps"]
    
    # Assert sequence of nodes: think -> execute_tool -> think -> generate_response
    nodes_executed = [step["node"] for step in steps]
    assert "think" in nodes_executed
    assert "execute_tool" in nodes_executed
    assert "generate_response" in nodes_executed


def test_agent_thinking_loop_simulation_sanitization():
    """Verify that simulation outputs include JSON for browser but sanitize it out for LLM prompts."""
    config = Config()
    config.LLM_PROVIDER = "mock"
    
    # Spying on messages sent to LLMClient
    generated_prompts = []
    
    class SpyingLLMClient(LLMClient):
        def generate(self, messages, tools=None):
            import copy
            generated_prompts.append(copy.deepcopy(messages))
            return super().generate(messages, tools)
            
    from src.features.tools.simulation.infrastructure.plot_generator import MatplotlibPlotGenerator
    llm_client = SpyingLLMClient(config)
    simulator = PhysicalPIDSimulator()
    plot_generator = MatplotlibPlotGenerator()
    sim_use_case = ExecuteSimulationUseCase(simulator, plot_generator)
    sim_tool = SimulationAgentTool(sim_use_case)
    
    thinking_loop = AgentThinkingLoop(llm_client, [sim_tool])
    
    # Message prompting a simulation
    messages = [{"role": "user", "content": "Run simulation with P=1.5, I=0.2, D=0.1"}]
    result = thinking_loop.run(messages)
    
    # 1. Verify that the final response contains the JSON block for the browser
    assert "STRUCTURED_DATA_JSON_START" in result["response"]
    assert "STRUCTURED_DATA_JSON_END" in result["response"]
    
    # 2. Verify that the intermediate prompt sent to the LLM was sanitized
    assert len(generated_prompts) >= 2
    second_prompt = generated_prompts[1]
    
    system_msgs = [m for m in second_prompt if m["role"] == "system"]
    assert len(system_msgs) > 0
    # The system message content sent to the LLM MUST NOT contain the JSON block
    for sys_m in system_msgs:
        assert "STRUCTURED_DATA_JSON_START" not in sys_m["content"]
        assert "STRUCTURED_DATA_JSON_END" not in sys_m["content"]

