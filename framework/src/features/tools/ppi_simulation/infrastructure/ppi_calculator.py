from src.features.tools.ppi_simulation.domain.ppi_simulation_entities import PPISimulationParameters, PPISimulationResult
from src.features.tools.ppi_simulation.application.ppi_simulation_use_case import PPISimulatorService

class PhysicalPPISimulator(PPISimulatorService):
    """
    DCモーターの物理モデルに基づいた離散時間数値積分による P-PI (位置比例・速度比例積分) 制御シミュレータの実装クラス。
    """
    def run_simulation(self, params: PPISimulationParameters) -> PPISimulationResult:
        dt = params.dt
        steps = params.steps
        kp = params.kp
        kvp = params.kvp
        kvi = params.kvi
        target = params.target

        # 物理特性定数（DCモーター - PhysicalPIDSimulatorと同一）
        J = 0.5   # 慣性モーメント (Moment of inertia)
        b = 0.1   # 粘性摩擦係数 (Viscous friction coefficient)

        # 台形速度プロファイル目標値の生成
        n_acc = int(steps * 0.25)
        n_dec = int(steps * 0.25)
        n_const = steps - n_acc - n_dec

        target_velocities = []
        for i in range(steps):
            if i < n_acc:
                v_ref = target * (i / n_acc) if n_acc > 0 else target
            elif i < n_acc + n_const:
                v_ref = target
            else:
                k = i - (n_acc + n_const)
                v_ref = target * (1.0 - k / n_dec) if n_dec > 0 else 0.0
            target_velocities.append(v_ref)

        # 目標位置プロファイル (速度プロファイルの離散積分)
        target_positions = []
        current_pos = 0.0
        for i in range(steps):
            target_positions.append(current_pos)
            current_pos += target_velocities[i] * dt

        # 各時間ステップにおけるシミュレーション結果ログ
        time_points = []
        positions = []
        velocities = []
        control_inputs = []
        errors = []

        # モーターの初期状態
        theta = 0.0   # 現在の角度位置 (Current motor position)
        omega = 0.0   # 現在の角速度 (Current motor velocity)
        v_integral = 0.0

        for i in range(steps):
            t = i * dt
            time_points.append(t)
            positions.append(theta)
            velocities.append(omega)

            v_ref = target_velocities[i]
            theta_ref = target_positions[i]

            # 位置偏差 (Position Error for outer loop)
            pos_error = theta_ref - theta

            # 速度追従偏差を記録 (Velocity tracking error for optimization/metrics)
            v_track_error = v_ref - omega
            errors.append(v_track_error)

            # --- P-PI カスケード制御アルゴリズム ---
            # 1. 外側（位置）ループ: P制御 -> 速度指令値 (v_cmd) を生成
            v_cmd = kp * pos_error
            # 速度指令値を安全限界内にクランプ (例: -15.0 rad/s から 15.0 rad/s)
            v_cmd = max(-15.0, min(15.0, v_cmd))

            # 2. 内側（速度）ループ: PI制御 -> トルク指令値 (u) を生成
            v_error = v_cmd - omega
            v_integral += v_error * dt
            # アンチワインドアップ (速度積分項の過剰蓄積リミッタ)
            v_integral = max(-10.0, min(10.0, v_integral))

            # 制御出力（トルク命令値）の計算
            u = kvp * v_error + kvi * v_integral
            # トルク制限（モーター出力の飽和制限）
            u = max(-20.0, min(20.0, u))
            control_inputs.append(u)

            # --- モーターの物理モデルシミュレーション ---
            d_omega = (u - b * omega) / J
            omega += d_omega * dt
            theta += omega * dt

        # シミュレーション結果をドメインオブジェクトとして返却
        return PPISimulationResult(
            time_points=time_points,
            positions=positions,
            velocities=velocities,
            target_velocities=target_velocities,
            control_inputs=control_inputs,
            errors=errors
        )
