import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from src.features.tools.ppi_simulation.application.ppi_simulation_use_case import PPIPlotGeneratorService


class MatplotlibPPIPlotGenerator(PPIPlotGeneratorService):
    def _plot_to_base64(self, fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"

    def generate_plots(self, time_points: list, velocities: list, target_velocities: list, torques: list) -> tuple[str, str]:
        """
        Generate two separate plots:
        1. Velocity tracking (target vs actual velocity)
        2. Applied torque (control input torque command)
        Returns them as a tuple of Base64 data URLs.
        """
        # Plot 1: Velocity Tracking
        fig1, ax1 = plt.subplots(figsize=(6, 3.5), dpi=150)
        fig1.patch.set_facecolor('#0e0d22')
        ax1.set_facecolor('#0e0d22')
        
        ax1.plot(time_points, target_velocities, color='#ff007f', linestyle='--', label='Target Velocity', linewidth=1.5)
        ax1.plot(time_points, velocities, color='#06b6d4', label='Actual Velocity', linewidth=2)
        
        ax1.set_title('P-PI Velocity Tracking Profile', color='white', fontsize=12, pad=10, fontweight='bold')
        ax1.set_xlabel('Time (seconds)', color='#a0a0c0', fontsize=10)
        ax1.set_ylabel('Velocity (rad/s)', color='#a0a0c0', fontsize=10)
        ax1.grid(True, color=(1.0, 1.0, 1.0, 0.07), linestyle=':')
        ax1.legend(facecolor='#1e1d3e', edgecolor='none', labelcolor='white', loc='lower right')
        ax1.tick_params(colors='#a0a0c0', which='both')
        for spine in ax1.spines.values():
            spine.set_color('#1e1d3e')
        fig1.tight_layout()
        vel_b64 = self._plot_to_base64(fig1)

        # Plot 2: Applied Torque
        fig2, ax2 = plt.subplots(figsize=(6, 3.5), dpi=150)
        fig2.patch.set_facecolor('#0e0d22')
        ax2.set_facecolor('#0e0d22')
        
        ax2.plot(time_points, torques, color='#10b981', label='Applied Torque', linewidth=2)
        
        ax2.set_title('P-PI Controller Control Output (Torque)', color='white', fontsize=12, pad=10, fontweight='bold')
        ax2.set_xlabel('Time (seconds)', color='#a0a0c0', fontsize=10)
        ax2.set_ylabel('Torque (N·m)', color='#a0a0c0', fontsize=10)
        ax2.grid(True, color=(1.0, 1.0, 1.0, 0.07), linestyle=':')
        ax2.legend(facecolor='#1e1d3e', edgecolor='none', labelcolor='white', loc='lower right')
        ax2.tick_params(colors='#a0a0c0', which='both')
        for spine in ax2.spines.values():
            spine.set_color('#1e1d3e')
        fig2.tight_layout()
        torque_b64 = self._plot_to_base64(fig2)

        return vel_b64, torque_b64
