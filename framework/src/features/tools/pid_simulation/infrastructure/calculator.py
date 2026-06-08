from src.features.tools.pid_simulation.domain.simulation_entities import SimulationParameters, SimulationResult
from src.features.tools.pid_simulation.application.simulation_use_case import SimulatorService

class PhysicalPIDSimulator(SimulatorService):
    """
    DCモーターの物理モデルに基づいた離散時間数値積分による PID 制御シミュレータの実装クラス。
    """
    def run_simulation(self, params: SimulationParameters) -> SimulationResult:
        dt = params.dt
        steps = params.steps
        kp = params.kp
        ki = params.ki
        kd = params.kd
        target = params.target

        # 物理特性定数（DCモーター）
        J = 0.5   # 慣性モーメント (Moment of inertia)
        b = 0.1   # 粘性摩擦係数 (Viscous friction coefficient)

        # 各時間ステップにおけるシミュレーション結果ログ
        time_points = []
        positions = []
        control_inputs = []
        errors = []

        # モーターの初期状態
        theta = 0.0   # 現在の角度位置 (Current motor position)
        omega = 0.0   # 現在の角速度 (Current motor velocity)
        prev_error = target - theta
        integral = 0.0

        for i in range(steps):
            t = i * dt
            time_points.append(t)
            positions.append(theta)

            error = target - theta
            errors.append(error)

            # --- PID 制御アルゴリズム ---
            # 積分項の蓄積
            integral += error * dt
            # アンチワインドアップ (積分項の過剰な蓄積を防ぐリミッタ)
            integral = max(-10.0, min(10.0, integral))
            
            # 微分項の計算
            derivative = (error - prev_error) / dt
            prev_error = error

            # 制御出力（トルク命令値）の計算
            u = kp * error + ki * integral + kd * derivative
            # トルク制限（モーター出力の飽和制限）
            u = max(-20.0, min(20.0, u))
            control_inputs.append(u)

            # --- モーターの物理モデルシミュレーション ---
            # トルク u から角加速度 d_omega を求め、角速度 omega と角度位置 theta を前進オイラー法で更新
            d_omega = (u - b * omega) / J
            omega += d_omega * dt
            theta += omega * dt

        # シミュレーション結果をドメインオブジェクトとして返却
        return SimulationResult(
            time_points=time_points,
            positions=positions,
            control_inputs=control_inputs,
            errors=errors
        )
