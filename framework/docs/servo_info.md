# ServoBot XM-430 Smart Servo Specifications

The ServoBot XM-430 is a high-performance, daisy-chainable smart actuator designed for robotic joint control. It features an integrated microcontroller, magnetic absolute encoder, and RS485 communication.

## Torque and Speed Performance

- **Operating Voltage**: 11.1V to 14.8V (Recommended: 12.0V)
- **Stall Torque**: 4.1 N·m at 12.0V, 4.5A
- **No Load Speed**: 55 RPM at 12.0V
- **Backlash**: Less than 0.15 degrees
- **Operating Angle**: 360 degrees continuous rotation or multi-turn absolute position control.

## PID Controller Settings

The onboard microcontroller executes a 1kHz PID control loop. For optimal stability and settling time under standard robotic load:

- **Proportional Gain (Kp)**: Default is 850 (recommended range: 500 - 1500). High Kp yields faster rise time but increases overshoot.
- **Integral Gain (Ki)**: Default is 0 (recommended range: 0 - 50). Use sparingly to avoid windup and instability.
- **Derivative Gain (Kd)**: Default is 0 (recommended range: 0 - 300). Dampens high-frequency oscillations.

For heavy inertia loads, it is recommended to set a custom current limit of 3.0A and scale down Kp to 600, while raising Kd to 150 to damp oscillations.
