from src.features.tools.ppi_bayesian_optimization.domain.ppi_bayesian_optimization_entities import (
    PPIOptimizationConfig,
    PPIOptimizationResult,
    PPIBayesianOptimizerService
)
from src.features.tools.ppi_simulation.application.ppi_simulation_use_case import PPISimulatorService

class OptimizePPIParametersUseCase:
    def __init__(
        self,
        optimizer: PPIBayesianOptimizerService,
        simulator: PPISimulatorService
    ):
        self.optimizer = optimizer
        self.simulator = simulator

    def execute(self, config: PPIOptimizationConfig) -> PPIOptimizationResult:
        """
        Run the Bayesian Optimization process to find optimal Kp, Kvp, Kvi parameters.
        """
        return self.optimizer.optimize(config, self.simulator)
