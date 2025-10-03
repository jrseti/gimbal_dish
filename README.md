# gimbal_dish
Pi project to control a simple X/Y gimbal for satellite dish pointing

## Overview

This Python script controls a satellite dish X-Y gimbal system using:
- **Raspberry Pi 3+ Model B** as the main controller
- **Dual TB9051FTG Motor Driver** from Pololu to control 2 JGY-370 DC motors
- **ADXL345 accelerometer** (I2C) from Adafruit for tilt sensing
- **MMC5603 magnetometer** (I2C) from Adafruit for azimuth sensing
- **PID control loops** for precise position control

## Hardware Setup

### Motor Driver (Dual TB9051FTG)
Connect the motor driver to the Raspberry Pi GPIO pins:
- Motor 1 (Azimuth) PWM: GPIO12
- Motor 1 Direction: GPIO5
- Motor 1 Enable: GPIO22
- Motor 2 (Tilt) PWM: GPIO13
- Motor 2 Direction: GPIO6
- Motor 2 Enable: GPIO23

### Sensors (I2C)
Both sensors connect to the I2C bus:
- SDA: GPIO2 (Pin 3)
- SCL: GPIO3 (Pin 5)
- Connect both sensors to the same I2C bus with appropriate pull-up resistors

### Motors
- Motor 1: Controls azimuth (horizontal rotation) - JGY-370 DC motor
- Motor 2: Controls tilt (vertical angle) - JGY-370 DC motor

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Enable I2C on Raspberry Pi:
```bash
sudo raspi-config
# Navigate to Interface Options -> I2C -> Enable
```

3. Verify I2C devices are detected:
```bash
sudo i2cdetect -y 1
```

## Usage

### Basic Usage

Run the script:
```bash
python3 gimbal_control.py
```

### Programmatic Usage

```python
from gimbal_control import GimbalController, MotorDriver, TiltSensor, AzimuthSensor
import board
import busio

# Initialize I2C
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize components
motor_driver = MotorDriver(
    pwm1_pin=12, pwm2_pin=13,
    dir1_pin=5, dir2_pin=6,
    en1_pin=22, en2_pin=23
)
tilt_sensor = TiltSensor(i2c)
azimuth_sensor = AzimuthSensor(i2c)

# Create controller
controller = GimbalController(motor_driver, tilt_sensor, azimuth_sensor)

# Set target position
controller.set_position(azimuth_deg=180.0, tilt_deg=45.0)

# Run control loop
controller.run(duration=60, update_rate=10)  # Run for 60 seconds at 10 Hz

# Cleanup
controller.cleanup()
```

### Setting Position

The `set_position()` function accepts:
- `azimuth_deg`: Azimuth angle in degrees (0-360°, 0=North)
- `tilt_deg`: Tilt angle in degrees (-90 to 90°, 0=horizontal)

Example:
```python
controller.set_position(azimuth_deg=180.0, tilt_deg=45.0)
```

## PID Tuning

The PID controller parameters can be adjusted in the `GimbalController` class:
```python
self.azimuth_pid = PID(Kp, Ki, Kd, setpoint=0)
self.tilt_pid = PID(Kp, Ki, Kd, setpoint=0)
```

Default values:
- Kp (Proportional): 1.0
- Ki (Integral): 0.1
- Kd (Derivative): 0.05

Tune these values based on your specific hardware and requirements.

## Features

- **Dual PID Control**: Separate PID controllers for azimuth and tilt
- **Continuous Monitoring**: Reads sensor data at configurable update rate (default 10 Hz)
- **Automatic Motor Adjustment**: Motors speeds are continuously adjusted to reach target position
- **Graceful Shutdown**: Properly stops motors and cleans up GPIO on exit
- **Error Handling**: Handles sensor failures and GPIO issues gracefully

## Notes

- The MMC5603 sensor implementation is a placeholder. You may need to implement the specific I2C protocol or find a compatible library.
- Pin assignments can be modified in the main() function
- Motor speeds are limited to -100 to 100 range
- The system uses BCM GPIO numbering

## License

MIT License - See LICENSE file for details
