import json
from abc import ABC, abstractmethod
from src.features.tools.ppi_simulation.domain.ppi_simulation_entities import PPISimulationParameters, PPISimulationResult

class PPISimulatorService(ABC):
    @abstractmethod
    def run_simulation(self, params: PPISimulationParameters) -> PPISimulationResult:
        pass


class PPIPlotGeneratorService(ABC):
    @abstractmethod
    def generate_plots(self, time_points: list, velocities: list, target_velocities: list, torques: list) -> tuple[str, str]:
        """
        Generate two waveform plots (velocity and torque) and return them as a tuple of Base64-encoded PNG data URLs.
        """
        pass


class ExecutePPISimulationUseCase:
    def __init__(self, simulator: PPISimulatorService, plot_generator: PPIPlotGeneratorService):
        self.simulator = simulator
        self.plot_generator = plot_generator

    def execute(self, kp: float, kvp: float, kvi: float, steps: int = 50) -> str:
        params = PPISimulationParameters(kp=kp, kvp=kvp, kvi=kvi, steps=steps)
        result = self.simulator.run_simulation(params)

        # Calculate metrics using velocities
        final_vel = result.velocities[-1]
        target = params.target
        ss_error = result.calculate_steady_state_error(target)
        
        # Check overshoot
        max_vel = max(result.velocities)
        overshoot = result.calculate_overshoot(target)
        overshoot_pct = (overshoot / target) * 100 if target != 0 else 0

        # Simple ASCII plot tracking velocities
        plot_lines = []
        width = 40
        min_v = min(0.0, min(result.velocities))
        max_v = max(target * 1.2, max(result.velocities))
        span = max_v - min_v if (max_v - min_v) > 0 else 1.0

        for step_idx in range(0, len(result.velocities), max(1, len(result.velocities) // 15)):
            vel = result.velocities[step_idx]
            tgt_vel = result.target_velocities[step_idx]
            t = result.time_points[step_idx]
            
            # Actual velocity character index
            vel_idx = int(((vel - min_v) / span) * (width - 1))
            vel_idx = max(0, min(width - 1, vel_idx))
            
            # Target velocity character index
            tgt_idx = int(((tgt_vel - min_v) / span) * (width - 1))
            tgt_idx = max(0, min(width - 1, tgt_idx))

            line_chars = [" "] * width
            line_chars[tgt_idx] = "|"
            line_chars[vel_idx] = "*"
            
            line_str = "".join(line_chars)
            plot_lines.append(f"t={t:4.1f}s: {line_str} (vel: {vel:.3f})")

        ascii_chart = "\n".join(plot_lines)

        # Generate the Base64 image of the plot
        velocity_image, torque_image = self.plot_generator.generate_plots(
            time_points=result.time_points,
            velocities=result.velocities,
            target_velocities=result.target_velocities,
            torques=result.control_inputs
        )

        # Prepare JSON string output so downstream steps can extract structured coordinates
        structured_data = {
            "image": velocity_image,
            "image_torque": torque_image,
            "metrics": {
                "steady_state_error": ss_error,
                "overshoot_percentage": overshoot_pct,
                "max_value": max_vel
            }
        }

        summary = (
            f"PPI Simulation completed (Kp={kp:.2f}, Kvp={kvp:.2f}, Kvi={kvi:.2f})\n"
            f"--------------------------------------------------\n"
            f"Target Velocity (Peak): {target:.2f}\n"
            f"Final Velocity: {final_vel:.4f}\n"
            f"Steady-State Error: {ss_error:.4f}\n"
            f"Max Overshoot: {overshoot:.4f} ({overshoot_pct:.1f}%)\n"
            f"--------------------------------------------------\n"
            f"Visual Profile (* = Velocity, | = Target Velocity):\n"
            f"{ascii_chart}\n"
            f"--------------------------------------------------\n"
            f"STRUCTURED_DATA_JSON_START\n"
            f"{json.dumps(structured_data)}\n"
            f"STRUCTURED_DATA_JSON_END"
        )
        return summary
