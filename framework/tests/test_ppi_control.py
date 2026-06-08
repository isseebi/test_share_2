import json
import os
import pytest
from src.shared.infrastructure.config import Config
from src.features.agent_brain.infrastructure.llm_client import LLMClient
from src.features.agent_brain.application.brain_loop import AgentThinkingLoop

# PPI Simulation
from src.features.tools.ppi_simulation.infrastructure.ppi_calculator import PhysicalPPISimulator
from src.features.tools.ppi_simulation.infrastructure.ppi_plot_generator import MatplotlibPPIPlotGenerator
from src.features.tools.ppi_simulation.application.ppi_simulation_use_case import ExecutePPISimulationUseCase
from src.features.tools.ppi_simulation.interface.ppi_simulation_tool import PPISimulationAgentTool

# PPI Bayesian Optimization
from src.features.tools.ppi_bayesian_optimization.infrastructure.ppi_optuna_optimizer import OptunaPPIBayesianOptimizer
from src.features.tools.ppi_bayesian_optimization.application.ppi_optimize_use_case import OptimizePPIParametersUseCase
from src.features.tools.ppi_bayesian_optimization.interface.ppi_bayesian_optimization_tool import PPIBayesianOptimizationTool
from src.features.tools.ppi_bayesian_optimization.domain.ppi_bayesian_optimization_entities import (
    PPIOptimizationBounds,
    PPIOptimizationConfig
)

# User Parameters
from src.features.tools.user_parameters.infrastructure.user_parameters_provider import FileUserParametersProvider
from src.features.tools.user_parameters.application.user_parameters_use_case import GetUserParametersUseCase
from src.features.tools.user_parameters.interface.user_parameters_tool import UserParametersAgentTool

# Web Search
from src.features.tools.web_search.infrastructure.ddg_search_client import DDGSearchClient
from src.features.tools.web_search.application.web_search_use_case import ExecuteWebSearchUseCase
from src.features.tools.web_search.interface.web_search_tool import WebSearchAgentTool


def test_ppi_simulation_math():
    """Verify that P-PI simulation calculates response correctly and generates plots."""
    simulator = PhysicalPPISimulator()
    plot_generator = MatplotlibPPIPlotGenerator()
    use_case = ExecutePPISimulationUseCase(simulator, plot_generator)

    # Run P-PI simulation
    result_text = use_case.execute(kp=2.2, kvp=1.5, kvi=0.6, steps=30)
    
    assert "PPI Simulation completed" in result_text
    assert "STRUCTURED_DATA_JSON_START" in result_text
    assert "STRUCTURED_DATA_JSON_END" in result_text
    
    # Extract and parse JSON
    json_part = result_text.split("STRUCTURED_DATA_JSON_START")[1].split("STRUCTURED_DATA_JSON_END")[0].strip()
    data = json.loads(json_part)
    
    assert "image" in data
    assert data["image"].startswith("data:image/png;base64,")
    assert "image_torque" in data
    assert data["image_torque"].startswith("data:image/png;base64,")
    assert "metrics" in data
    assert "steady_state_error" in data["metrics"]
    assert "overshoot_percentage" in data["metrics"]


def test_ppi_bayesian_optimization():
    """Verify that P-PI Bayesian Optimization successfully finds tuned gains."""
    simulator = PhysicalPPISimulator()
    optimizer = OptunaPPIBayesianOptimizer()
    use_case = OptimizePPIParametersUseCase(optimizer, simulator)

    bounds = PPIOptimizationBounds(
        kp_min=1.0, kp_max=4.0,
        kvp_min=0.5, kvp_max=2.5,
        kvi_min=0.0, kvi_max=1.0
    )
    config = PPIOptimizationConfig(
        bounds=bounds,
        n_trials=10,
        target=1.0,
        steps=20
    )

    result = use_case.execute(config)
    
    assert result.best_kp >= 1.0
    assert result.best_kvp >= 0.5
    assert result.best_kvi >= 0.0
    assert len(result.trials) == 10
    assert result.best_score < 1e9


def test_user_parameters_retrieval(tmp_path):
    """Verify that the user parameters tool retrieves parameter JSON and creates fallback config if missing."""
    temp_json = tmp_path / "test_user_parameters.json"
    
    # 1. First run: file is missing, should create it with defaults
    provider = FileUserParametersProvider(str(temp_json))
    use_case = GetUserParametersUseCase(provider)
    tool = UserParametersAgentTool(use_case)
    
    result = tool.execute({})
    data = json.loads(result)
    
    assert data["status"] == "success"
    assert "parameters" in data
    assert data["parameters"]["kp"] == 2.5
    assert "description" in data
    assert os.path.exists(temp_json)

    # 2. Second run: write custom value and read it
    with open(temp_json, "w", encoding="utf-8") as f:
        json.dump({
            "system_name": "Test System XM",
            "kp": 9.9,
            "kvp": 8.8,
            "kvi": 7.7,
            "notes": "Custom test notes"
        }, f)
        
    result_custom = tool.execute({})
    data_custom = json.loads(result_custom)
    
    assert data_custom["system_name"] == "Test System XM"
    assert data_custom["parameters"]["kp"] == 9.9
    assert data_custom["parameters"]["kvp"] == 8.8
    assert data_custom["parameters"]["kvi"] == 7.7


def test_web_search_execution():
    """Verify that the web search use case executes DDG client successfully."""
    client = DDGSearchClient()
    use_case = ExecuteWebSearchUseCase(client)
    tool = WebSearchAgentTool(use_case)

    # Testing both generic and fallback-keyword search
    result_1 = tool.execute({"query": "Dynamixel xm-430 specifications"})
    assert "DuckDuckGo search results" in result_1
    assert "XM430" in result_1

    result_2 = tool.execute({"query": "arbitrary query term"})
    assert "DuckDuckGo search results" in result_2


def test_agent_thinking_loop_ppi_tools():
    """Verify that the LangGraph Agent loop routes queries to the new PPI and Web Search tools."""
    config = Config()
    config.LLM_PROVIDER = "mock"
    
    llm_client = LLMClient(config)
    
    search_client = DDGSearchClient()
    ppi_simulator = PhysicalPPISimulator()
    ppi_plot_generator = MatplotlibPPIPlotGenerator()
    ppi_opt_tool = OptunaPPIBayesianOptimizer()
    user_params_provider = FileUserParametersProvider()

    web_search_tool = WebSearchAgentTool(ExecuteWebSearchUseCase(search_client))
    ppi_sim_tool = PPISimulationAgentTool(ExecutePPISimulationUseCase(ppi_simulator, ppi_plot_generator))
    ppi_opt_tool_wrapper = PPIBayesianOptimizationTool(OptimizePPIParametersUseCase(ppi_opt_tool, ppi_simulator))
    user_params_tool = UserParametersAgentTool(GetUserParametersUseCase(user_params_provider))

    thinking_loop = AgentThinkingLoop(
        llm_client,
        [web_search_tool, ppi_sim_tool, ppi_opt_tool_wrapper, user_params_tool]
    )

    # 1. PPI Simulation Query
    result_sim = thinking_loop.run([{"role": "user", "content": "Run PPI control simulation with kp=2.2, kvp=1.5, kvi=0.6"}])
    assert "I have run the PPI control simulation" in result_sim["response"]
    assert "STRUCTURED_DATA_JSON_START" in result_sim["response"]

    # 2. PPI Optimization Query
    result_opt = thinking_loop.run([{"role": "user", "content": "Optimize PPI controller parameters"}])
    assert "I have run the PPI parameter optimization" in result_opt["response"]
    assert "best_params" in result_opt["response"]

    # 3. User Parameters Query
    result_params = thinking_loop.run([{"role": "user", "content": "Get the current user parameters"}])
    assert "I have retrieved the user system parameters" in result_params["response"]
    assert "parameters" in result_params["response"]

    # 4. Web Search Query
    result_web = thinking_loop.run([{"role": "user", "content": "Perform web search for Dynamixel specs"}])
    assert "I have performed a web search using DuckDuckGo" in result_web["response"]
