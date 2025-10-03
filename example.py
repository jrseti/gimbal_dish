#!/usr/bin/env python3
"""
Example usage of the gimbal control system
Demonstrates how to use the GimbalController to point the dish
"""

from gimbal_control import GimbalController, MotorDriver, TiltSensor, AzimuthSensor
import time

try:
    import board
    import busio
except ImportError:
    print("Warning: board/busio not available, using mock mode")
    board = None
    busio = None


def example_point_to_satellite():
    """Example: Point the dish to a specific satellite position"""
    print("=" * 60)
    print("Example: Pointing to satellite")
    print("=" * 60)
    
    # Initialize I2C bus
    i2c = None
    if board and busio:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
        except Exception as e:
            print(f"Could not initialize I2C: {e}")
    
    # Initialize motor driver with pin configuration
    motor_driver = MotorDriver(
        pwm1_pin=12,    # Motor 1 PWM
        pwm2_pin=13,    # Motor 2 PWM
        dir1_pin=5,     # Motor 1 Direction
        dir2_pin=6,     # Motor 2 Direction
        en1_pin=22,     # Motor 1 Enable
        en2_pin=23      # Motor 2 Enable
    )
    
    # Initialize sensors
    tilt_sensor = TiltSensor(i2c)
    azimuth_sensor = AzimuthSensor(i2c)
    
    # Create controller
    controller = GimbalController(motor_driver, tilt_sensor, azimuth_sensor)
    
    try:
        # Example 1: Point to 180° azimuth, 45° elevation
        print("\n1. Pointing to azimuth=180°, tilt=45°")
        controller.set_position(azimuth_deg=180.0, tilt_deg=45.0)
        controller.run(duration=10, update_rate=10)
        
        # Example 2: Point to 90° azimuth, 30° elevation
        print("\n2. Pointing to azimuth=90°, tilt=30°")
        controller.set_position(azimuth_deg=90.0, tilt_deg=30.0)
        controller.run(duration=10, update_rate=10)
        
        # Example 3: Point to 270° azimuth, 60° elevation
        print("\n3. Pointing to azimuth=270°, tilt=60°")
        controller.set_position(azimuth_deg=270.0, tilt_deg=60.0)
        controller.run(duration=10, update_rate=10)
        
    finally:
        controller.cleanup()
        print("\nExample completed")


def example_manual_control():
    """Example: Manual step-by-step control"""
    print("=" * 60)
    print("Example: Manual control with update steps")
    print("=" * 60)
    
    # Initialize I2C bus
    i2c = None
    if board and busio:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
        except Exception as e:
            print(f"Could not initialize I2C: {e}")
    
    # Initialize motor driver
    motor_driver = MotorDriver(
        pwm1_pin=12, pwm2_pin=13,
        dir1_pin=5, dir2_pin=6,
        en1_pin=22, en2_pin=23
    )
    
    # Initialize sensors
    tilt_sensor = TiltSensor(i2c)
    azimuth_sensor = AzimuthSensor(i2c)
    
    # Create controller
    controller = GimbalController(motor_driver, tilt_sensor, azimuth_sensor)
    
    try:
        # Set target
        controller.set_position(azimuth_deg=180.0, tilt_deg=45.0)
        
        # Manual control loop - run 100 iterations
        print("Running 100 control iterations...")
        for i in range(100):
            current_az, current_tilt, speed_az, speed_tilt = controller.update()
            
            if i % 10 == 0:  # Print every 10 iterations
                print(f"Iteration {i}: Az={current_az:.2f}° Tilt={current_tilt:.2f}°")
            
            time.sleep(0.1)  # 10 Hz update rate
        
    finally:
        controller.cleanup()
        print("\nManual control example completed")


if __name__ == "__main__":
    print("Gimbal Control Examples")
    print()
    
    # Run example 1
    example_point_to_satellite()
    
    print("\n" + "=" * 60 + "\n")
    
    # Run example 2
    example_manual_control()
