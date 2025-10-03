#!/usr/bin/env python3
"""
Gimbal Dish Control System
Controls a satellite dish X-Y gimbal using:
- Dual TB9051FTG Motor Driver for Raspberry Pi (Pololu)
- ADXL345 accelerometer for tilt sensing (I2C)
- MMC5603 magnetometer for azimuth sensing (I2C)
"""

import time
import math

try:
    import board
    import busio
except ImportError:
    print("Warning: board/busio not available")
    board = None
    busio = None

try:
    import adafruit_adxl34x
except ImportError:
    print("Warning: adafruit_adxl34x not available")
    adafruit_adxl34x = None

try:
    from simple_pid import PID
except ImportError:
    print("Warning: simple_pid not available, using basic PID implementation")
    # Basic PID implementation as fallback
    class PID:
        def __init__(self, Kp, Ki, Kd, setpoint=0):
            self.Kp = Kp
            self.Ki = Ki
            self.Kd = Kd
            self.setpoint = setpoint
            self.output_limits = (-100, 100)
            self._integral = 0
            self._last_error = 0
            self._last_time = time.time()
        
        def __call__(self, input_value):
            error = self.setpoint - input_value
            current_time = time.time()
            dt = current_time - self._last_time
            
            if dt > 0:
                # Proportional term
                p_term = self.Kp * error
                
                # Integral term
                self._integral += error * dt
                i_term = self.Ki * self._integral
                
                # Derivative term
                d_term = self.Kd * (error - self._last_error) / dt if dt > 0 else 0
                
                # Calculate output
                output = p_term + i_term + d_term
                
                # Apply limits
                output = max(self.output_limits[0], min(self.output_limits[1], output))
                
                self._last_error = error
                self._last_time = current_time
                
                return output
            return 0

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Warning: RPi.GPIO not available, using mock GPIO")
    GPIO = None


class MotorDriver:
    """Interface for Dual TB9051FTG Motor Driver"""
    
    def __init__(self, pwm1_pin, pwm2_pin, dir1_pin, dir2_pin, en1_pin=None, en2_pin=None):
        """
        Initialize motor driver
        pwm1_pin: PWM pin for motor 1 (azimuth)
        pwm2_pin: PWM pin for motor 2 (tilt)
        dir1_pin: Direction pin for motor 1
        dir2_pin: Direction pin for motor 2
        en1_pin: Enable pin for motor 1 (optional)
        en2_pin: Enable pin for motor 2 (optional)
        """
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            
            # Motor 1 (Azimuth)
            self.pwm1_pin = pwm1_pin
            self.dir1_pin = dir1_pin
            GPIO.setup(pwm1_pin, GPIO.OUT)
            GPIO.setup(dir1_pin, GPIO.OUT)
            self.motor1_pwm = GPIO.PWM(pwm1_pin, 1000)  # 1kHz frequency
            self.motor1_pwm.start(0)
            
            # Motor 2 (Tilt)
            self.pwm2_pin = pwm2_pin
            self.dir2_pin = dir2_pin
            GPIO.setup(pwm2_pin, GPIO.OUT)
            GPIO.setup(dir2_pin, GPIO.OUT)
            self.motor2_pwm = GPIO.PWM(pwm2_pin, 1000)  # 1kHz frequency
            self.motor2_pwm.start(0)
            
            # Enable pins (if provided)
            if en1_pin:
                self.en1_pin = en1_pin
                GPIO.setup(en1_pin, GPIO.OUT)
                GPIO.output(en1_pin, GPIO.HIGH)
            
            if en2_pin:
                self.en2_pin = en2_pin
                GPIO.setup(en2_pin, GPIO.OUT)
                GPIO.output(en2_pin, GPIO.HIGH)
        else:
            self.motor1_pwm = None
            self.motor2_pwm = None
    
    def set_motor1_speed(self, speed):
        """
        Set motor 1 (azimuth) speed
        speed: -100 to 100 (negative = reverse, positive = forward)
        """
        if not GPIO:
            print(f"Mock: Setting motor 1 speed to {speed}")
            return
            
        direction = GPIO.HIGH if speed >= 0 else GPIO.LOW
        GPIO.output(self.dir1_pin, direction)
        self.motor1_pwm.ChangeDutyCycle(min(abs(speed), 100))
    
    def set_motor2_speed(self, speed):
        """
        Set motor 2 (tilt) speed
        speed: -100 to 100 (negative = reverse, positive = forward)
        """
        if not GPIO:
            print(f"Mock: Setting motor 2 speed to {speed}")
            return
            
        direction = GPIO.HIGH if speed >= 0 else GPIO.LOW
        GPIO.output(self.dir2_pin, direction)
        self.motor2_pwm.ChangeDutyCycle(min(abs(speed), 100))
    
    def stop(self):
        """Stop both motors"""
        self.set_motor1_speed(0)
        self.set_motor2_speed(0)
    
    def cleanup(self):
        """Cleanup GPIO"""
        if GPIO:
            self.stop()
            self.motor1_pwm.stop()
            self.motor2_pwm.stop()
            GPIO.cleanup()


class TiltSensor:
    """Interface for ADXL345 accelerometer"""
    
    def __init__(self, i2c):
        """Initialize ADXL345 sensor"""
        self.sensor = None
        if not adafruit_adxl34x or not i2c:
            print("Warning: ADXL345 not available (missing library or I2C)")
            return
            
        try:
            self.sensor = adafruit_adxl34x.ADXL345(i2c)
        except Exception as e:
            print(f"Warning: Could not initialize ADXL345: {e}")
            self.sensor = None
    
    def get_tilt(self):
        """
        Get tilt angle in degrees
        Returns angle from -90 to 90 degrees (0 = horizontal)
        """
        if not self.sensor:
            return 0.0
            
        try:
            x, y, z = self.sensor.acceleration
            # Calculate tilt angle from accelerometer
            # Using Y-axis as the tilt axis
            tilt = math.degrees(math.atan2(y, math.sqrt(x*x + z*z)))
            return tilt
        except Exception as e:
            print(f"Error reading tilt: {e}")
            return 0.0


class AzimuthSensor:
    """Interface for MMC5603 magnetometer"""
    
    def __init__(self, i2c):
        """Initialize MMC5603 sensor"""
        # Note: There isn't a standard Adafruit library for MMC5603 yet
        # This is a placeholder implementation
        # In practice, you'd need to use the I2C bus directly or find a suitable library
        self.i2c = i2c
        self.sensor = None
        try:
            # Placeholder for MMC5603 initialization
            # You would need to implement the specific I2C protocol for MMC5603
            print("MMC5603 initialization placeholder")
        except Exception as e:
            print(f"Warning: Could not initialize MMC5603: {e}")
    
    def get_azimuth(self):
        """
        Get azimuth angle in degrees
        Returns angle from 0 to 360 degrees (0 = North)
        """
        if not self.sensor:
            # Placeholder return
            return 0.0
            
        try:
            # Placeholder for reading magnetometer data
            # In practice, you'd read X, Y, Z magnetic field values
            # and calculate heading: azimuth = math.degrees(math.atan2(y, x))
            return 0.0
        except Exception as e:
            print(f"Error reading azimuth: {e}")
            return 0.0


class GimbalController:
    """Main gimbal controller with PID loops"""
    
    def __init__(self, motor_driver, tilt_sensor, azimuth_sensor):
        """Initialize gimbal controller"""
        self.motor_driver = motor_driver
        self.tilt_sensor = tilt_sensor
        self.azimuth_sensor = azimuth_sensor
        
        # PID controllers
        # Tune these values based on your system
        self.azimuth_pid = PID(1.0, 0.1, 0.05, setpoint=0)
        self.azimuth_pid.output_limits = (-100, 100)
        
        self.tilt_pid = PID(1.0, 0.1, 0.05, setpoint=0)
        self.tilt_pid.output_limits = (-100, 100)
        
        self.target_azimuth = 0.0
        self.target_tilt = 0.0
        self.running = False
    
    def set_position(self, azimuth_deg, tilt_deg):
        """
        Set target position for the gimbal
        azimuth_deg: Target azimuth in degrees (0-360)
        tilt_deg: Target tilt in degrees (-90 to 90)
        """
        # Normalize azimuth to 0-360
        self.target_azimuth = azimuth_deg % 360
        
        # Clamp tilt to valid range
        self.target_tilt = max(-90, min(90, tilt_deg))
        
        # Update PID setpoints
        self.azimuth_pid.setpoint = self.target_azimuth
        self.tilt_pid.setpoint = self.target_tilt
        
        print(f"Target position set: Azimuth={self.target_azimuth}°, Tilt={self.target_tilt}°")
    
    def _normalize_azimuth_error(self, error):
        """Normalize azimuth error to -180 to 180 range"""
        while error > 180:
            error -= 360
        while error < -180:
            error += 360
        return error
    
    def update(self):
        """Single update cycle - read sensors and adjust motors"""
        # Read current positions
        current_tilt = self.tilt_sensor.get_tilt()
        current_azimuth = self.azimuth_sensor.get_azimuth()
        
        # Calculate azimuth error (normalized to -180 to 180)
        azimuth_error = self._normalize_azimuth_error(
            self.target_azimuth - current_azimuth
        )
        
        # Calculate motor speeds using PID
        # For azimuth, we need to handle the circular nature of angles
        azimuth_speed = self.azimuth_pid(current_azimuth + azimuth_error)
        tilt_speed = self.tilt_pid(current_tilt)
        
        # Apply motor speeds
        self.motor_driver.set_motor1_speed(azimuth_speed)
        self.motor_driver.set_motor2_speed(tilt_speed)
        
        return current_azimuth, current_tilt, azimuth_speed, tilt_speed
    
    def run(self, duration=None, update_rate=10):
        """
        Run the control loop
        duration: How long to run in seconds (None = run indefinitely)
        update_rate: Updates per second
        """
        self.running = True
        start_time = time.time()
        
        print(f"Starting gimbal control loop (update rate: {update_rate} Hz)")
        print("Press Ctrl+C to stop")
        
        try:
            while self.running:
                # Check if duration exceeded
                if duration and (time.time() - start_time) > duration:
                    break
                
                # Update control loop
                current_az, current_tilt, speed_az, speed_tilt = self.update()
                
                # Print status
                print(f"Az: {current_az:6.2f}° (target: {self.target_azimuth:6.2f}°) "
                      f"| Tilt: {current_tilt:6.2f}° (target: {self.target_tilt:6.2f}°) "
                      f"| Speed Az: {speed_az:6.2f} | Speed Tilt: {speed_tilt:6.2f}")
                
                # Sleep to maintain update rate
                time.sleep(1.0 / update_rate)
                
        except KeyboardInterrupt:
            print("\nStopping gimbal control...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the control loop and motors"""
        self.running = False
        self.motor_driver.stop()
        print("Gimbal stopped")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        self.motor_driver.cleanup()


def main():
    """Main entry point"""
    print("Gimbal Dish Control System")
    print("=" * 50)
    
    # Initialize I2C bus
    i2c = None
    if board and busio:
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
        except Exception as e:
            print(f"Warning: Could not initialize I2C: {e}")
    else:
        print("Warning: I2C not available (board/busio not imported)")
    
    # Initialize motor driver
    # Pin configuration for Dual TB9051FTG Motor Driver
    # Adjust these pins based on your wiring
    motor_driver = MotorDriver(
        pwm1_pin=12,    # Motor 1 PWM (GPIO12)
        pwm2_pin=13,    # Motor 2 PWM (GPIO13)
        dir1_pin=5,     # Motor 1 Direction (GPIO5)
        dir2_pin=6,     # Motor 2 Direction (GPIO6)
        en1_pin=22,     # Motor 1 Enable (GPIO22)
        en2_pin=23      # Motor 2 Enable (GPIO23)
    )
    
    # Initialize sensors
    tilt_sensor = TiltSensor(i2c) if i2c else None
    azimuth_sensor = AzimuthSensor(i2c) if i2c else None
    
    if not tilt_sensor:
        print("Warning: Tilt sensor not available")
        tilt_sensor = TiltSensor(None)
    
    if not azimuth_sensor:
        print("Warning: Azimuth sensor not available")
        azimuth_sensor = AzimuthSensor(None)
    
    # Create gimbal controller
    controller = GimbalController(motor_driver, tilt_sensor, azimuth_sensor)
    
    try:
        # Example usage: Set target position
        controller.set_position(azimuth_deg=180.0, tilt_deg=45.0)
        
        # Run control loop
        controller.run(duration=None, update_rate=10)
        
    finally:
        controller.cleanup()
        print("Cleanup complete")


if __name__ == "__main__":
    main()
