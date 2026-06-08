from abc import ABC, abstractmethod
from typing import List, Any, Protocol

class PPIOptimizationBounds:
    def __init__(
        self,
        kp_min: float = 0.0,
        kp_max: float = 10.0,
        kvp_min: float = 0.0,
        kvp_max: float = 10.0,
        kvi_min: float = 0.0,
        kvi_max: float = 10.0
    ):
        self.kp_min = kp_min
        self.kp_max = kp_max
        self.kvp_min = kvp_min
        self.kvp_max = kvp_max
        self.kvi_min = kvi_min
        self.kvi_max = kvi_max


class PPIOptimizationConfig:
    def __init__(
        self,
        bounds: PPIOptimizationBounds,
        n_trials: int = 50,
        target: float = 1.0,
        steps: int = 50,
        dt: float = 0.1,
        weight_itae: float = 1.0,
        weight_overshoot: float = 2.0,
        weight_steady_state: float = 5.0
    ):
        self.bounds = bounds
        self.n_trials = n_trials
        self.target = target
        self.steps = steps
        self.dt = dt
        self.weight_itae = weight_itae
        self.weight_overshoot = weight_overshoot
        self.weight_steady_state = weight_steady_state


class PPIOptimizationTrial:
    def __init__(
        self,
        number: int,
        kp: float,
        kvp: float,
        kvi: float,
        score: float
    ):
        self.number = number
        self.kp = kp
        self.kvp = kvp
        self.kvi = kvi
        self.score = score


class PPIOptimizationResult:
    def __init__(
        self,
        best_kp: float,
        best_kvp: float,
        best_kvi: float,
        best_score: float,
        trials: List[PPIOptimizationTrial]
    ):
        self.best_kp = best_kp
        self.best_kvp = best_kvp
        self.best_kvi = best_kvi
        self.best_score = best_score
        self.trials = trials


class PPISimulatorLike(Protocol):
    """
    Protocol to represent a simulator for P-PI control.
    Avoids direct domain-to-domain dependency to comply with architecture rules.
    """
    def run_simulation(self, params: Any) -> Any:
        ...


class PPIBayesianOptimizerService(ABC):
    @abstractmethod
    def optimize(
        self,
        config: PPIOptimizationConfig,
        simulator: PPISimulatorLike
    ) -> PPIOptimizationResult:
        pass
