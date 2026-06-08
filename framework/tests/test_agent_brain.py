import pytest
from src.shared.infrastructure.config import Config
from src.features.agent_brain.infrastructure.llm_client import LLMClient
from src.features.agent_brain.application.brain_loop import AgentThinkingLoop
from src.features.tools.search.infrastructure.document_store import FileSystemDocumentStore
from src.features.tools.search.application.search_use_case import ExecuteSearchUseCase
from src.features.tools.search.interface.search_tool import SearchAgentTool
from src.features.tools.pid_simulation.infrastructure.calculator import PhysicalPIDSimulator
from src.features.tools.pid_simulation.application.simulation_use_case import ExecuteSimulationUseCase
from src.features.tools.pid_simulation.interface.simulation_tool import SimulationAgentTool

def test_pid_simulation_math():
    """Verify that PID simulation executes and produces correct trajectory limits."""
    from src.features.tools.pid_simulation.infrastructure.plot_generator import MatplotlibPlotGenerator
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


def test_llm_client_routing_claude():
    """Verify that LLMClient correctly routes 'claude' provider to Bedrock and instantiates ChatBedrock."""
    from unittest.mock import MagicMock, patch
    
    mock_chat_bedrock = MagicMock()
    
    # We patch ChatBedrock to return our mock object
    with patch("src.features.agent_brain.infrastructure.llm_client.ChatBedrock", return_value=mock_chat_bedrock) as mock_class:
        config = Config()
        config.LLM_PROVIDER = "claude"
        config.AWS_REGION = "us-east-1"
        config.BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet"
        config.AWS_ACCESS_KEY_ID = "test-key"
        config.AWS_SECRET_ACCESS_KEY = "test-secret"
        config.AWS_SESSION_TOKEN = "test-token"
        
        client = LLMClient(config)
        assert client.provider == "claude"
        
        # When we generate response, it should invoke the Bedrock model
        mock_chat_bedrock.invoke.return_value = MagicMock(content="Hello from Bedrock")
        
        response_text, tool_calls = client.generate([{"role": "user", "content": "hello"}])
        
        assert response_text == "Hello from Bedrock"
        assert tool_calls == []
        
        # Verify ChatBedrock was instantiated with correct arguments
        mock_class.assert_called_once_with(
            model_id="anthropic.claude-3-5-sonnet",
            region_name="us-east-1",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            aws_session_token="test-token"
        )


def test_agent_thinking_loop_max_loops_limiter():
    """Verify that AgentThinkingLoop halts execution after reaching max_loops limit."""
    from src.features.agent_brain.application.brain_loop import AgentThinkingLoop, LLMService, AgentTool
    
    # Create a dummy tool and LLMService
    class DummyLLM(LLMService):
        def generate(self, messages, tools=None):
            # LLM always returns a tool call to simulate an infinite loop
            return "Thinking...", [{"name": "dummy_tool", "args": {}}]
            
    class DummyTool(AgentTool):
        @property
        def name(self) -> str:
            return "dummy_tool"
            
        @property
        def description(self) -> str:
            return "A dummy tool"
            
        def execute(self, args) -> str:
            return "Tool output"
            
    llm = DummyLLM()
    tool = DummyTool()
    
    # We configure max_loops = 2
    thinking_loop = AgentThinkingLoop(llm, [tool], max_loops=2)
    
    result = thinking_loop.run([{"role": "user", "content": "Keep calling the tool"}])
    
    # Check that execution was halted and response contains the limit warning
    assert "上限回数" in result["response"]
    assert "2回" in result["response"]
    assert result["loop_count"] == 2



