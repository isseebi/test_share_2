import optuna
from typing import List
from src.features.tools.ppi_bayesian_optimization.domain.ppi_bayesian_optimization_entities import (
    PPIOptimizationConfig,
    PPIOptimizationResult,
    PPIOptimizationTrial,
    PPIBayesianOptimizerService,
    PPISimulatorLike
)
from src.features.tools.ppi_simulation.domain.ppi_simulation_entities import PPISimulationParameters

# Suppress Optuna output logs during optimization to keep output clean
optuna.logging.set_verbosity(optuna.logging.WARNING)

class OptunaPPIBayesianOptimizer(PPIBayesianOptimizerService):
    def optimize(
        self,
        config: PPIOptimizationConfig,
        simulator: PPISimulatorLike
    ) -> PPIOptimizationResult:
        """
        Optimize PPI parameters using Optuna's Tree-structured Parzen Estimator (TPE) algorithm.
        """
        sampler = optuna.samplers.TPESampler(seed=42)
        study = optuna.create_study(direction="minimize", sampler=sampler)

        def objective(trial: optuna.Trial) -> float:
            # Suggest Kp, Kvp, Kvi values within their respective bounds
            kp = trial.suggest_float("kp", config.bounds.kp_min, config.bounds.kp_max)
            kvp = trial.suggest_float("kvp", config.bounds.kvp_min, config.bounds.kvp_max)
            kvi = trial.suggest_float("kvi", config.bounds.kvi_min, config.bounds.kvi_max)

            # Build simulation parameters
            params = PPISimulationParameters(
                kp=kp,
                kvp=kvp,
                kvi=kvi,
                target=config.target,
                steps=config.steps,
                dt=config.dt
            )

            # Run the simulation
            result = simulator.run_simulation(params)

            # Evaluate metrics from the simulation results
            itae = result.calculate_itae(config.dt)
            overshoot = result.calculate_overshoot(config.target)
            steady_state_error = result.calculate_steady_state_error(config.target)

            # Compute weighted loss function
            loss = (
                config.weight_itae * itae
                + config.weight_overshoot * overshoot
                + config.weight_steady_state * steady_state_error
            )

            # Handle edge cases where simulation might fail or diverge
            if loss != loss or loss == float('inf') or loss == float('-inf'):
                return 1e9

            return loss

        # Run optimization
        study.optimize(objective, n_trials=config.n_trials)

        # Collect trials history
        trials: List[PPIOptimizationTrial] = []
        for t in study.trials:
            # Skip trials that did not complete successfully
            if t.state != optuna.trial.TrialState.COMPLETE:
                continue
            
            trials.append(
                PPIOptimizationTrial(
                    number=t.number,
                    kp=t.params.get("kp", 0.0),
                    kvp=t.params.get("kvp", 0.0),
                    kvi=t.params.get("kvi", 0.0),
                    score=t.value if t.value is not None else 1e9
                )
            )

        best_params = study.best_params
        best_score = study.best_value

        return PPIOptimizationResult(
            best_kp=best_params.get("kp", 0.0),
            best_kvp=best_params.get("kvp", 0.0),
            best_kvi=best_params.get("kvi", 0.0),
            best_score=best_score,
            trials=trials
        )
