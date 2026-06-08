import optuna
from typing import List
from src.features.tools.pid_bayesian_optimization.domain.bayesian_optimization_entities import (
    OptimizationConfig,
    OptimizationResult,
    OptimizationTrial,
    BayesianOptimizerService,
    SimulatorLike
)
from src.features.tools.pid_simulation.domain.simulation_entities import SimulationParameters

# Suppress Optuna output logs during optimization to keep output clean, but let's do it gently.
optuna.logging.set_verbosity(optuna.logging.WARNING)

class OptunaBayesianOptimizer(BayesianOptimizerService):
    def optimize(
        self,
        config: OptimizationConfig,
        simulator: SimulatorLike
    ) -> OptimizationResult:
        """
        Optimize PID parameters using Optuna's Tree-structured Parzen Estimator (TPE) algorithm.
        """
        # We explicitly use TPESampler for Bayesian optimization
        sampler = optuna.samplers.TPESampler(seed=42)
        study = optuna.create_study(direction="minimize", sampler=sampler)

        def objective(trial: optuna.Trial) -> float:
            # Suggest Kp, Ki, Kd values within their respective bounds
            kp = trial.suggest_float("kp", config.bounds.kp_min, config.bounds.kp_max)
            ki = trial.suggest_float("ki", config.bounds.ki_min, config.bounds.ki_max)
            kd = trial.suggest_float("kd", config.bounds.kd_min, config.bounds.kd_max)

            # Build simulation parameters
            params = SimulationParameters(
                kp=kp,
                ki=ki,
                kd=kd,
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
        trials: List[OptimizationTrial] = []
        for t in study.trials:
            # Skip trials that did not complete successfully
            if t.state != optuna.trial.TrialState.COMPLETE:
                continue
            
            trials.append(
                OptimizationTrial(
                    number=t.number,
                    kp=t.params.get("kp", 0.0),
                    ki=t.params.get("ki", 0.0),
                    kd=t.params.get("kd", 0.0),
                    score=t.value if t.value is not None else 1e9
                )
            )

        best_params = study.best_params
        best_score = study.best_value

        return OptimizationResult(
            best_kp=best_params.get("kp", 0.0),
            best_ki=best_params.get("ki", 0.0),
            best_kd=best_params.get("kd", 0.0),
            best_score=best_score,
            trials=trials
        )
