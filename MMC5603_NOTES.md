# MMC5603 Sensor Implementation Notes

## Overview
The MMC5603 is a magnetometer used for azimuth (compass heading) sensing in the gimbal system. As of the current implementation, the Adafruit CircuitPython library for MMC5603 may not be available, so the sensor integration includes a placeholder implementation.

## Current Implementation Status

The `AzimuthSensor` class in `gimbal_control.py` contains placeholder code for the MMC5603. To fully integrate this sensor, you have two options:

### Option 1: Use Direct I2C Communication

The MMC5603 has a default I2C address of 0x30. You can implement direct register communication:

```python
class AzimuthSensor:
    MMC5603_I2C_ADDR = 0x30
    
    # Register addresses (example - check datasheet)
    REG_XOUT_0 = 0x00
    REG_XOUT_1 = 0x01
    # ... etc
    
    def __init__(self, i2c):
        self.i2c = i2c
        self.address = self.MMC5603_I2C_ADDR
        # Initialize sensor
        # Write to control registers as needed
    
    def get_azimuth(self):
        # Read X and Y magnetic field data
        # Calculate heading: azimuth = math.atan2(y, x) * 180 / math.pi
        pass
```

### Option 2: Wait for Library Support

Check for an available library:
- Adafruit may release a CircuitPython library for MMC5603
- Third-party libraries may be available on GitHub
- The similar QMC5883L libraries may provide reference implementations

## Implementation Guide

1. **Identify the MMC5603 on I2C bus:**
   ```bash
   sudo i2cdetect -y 1
   ```
   Look for device at address 0x30

2. **Read the datasheet:**
   - Download the MMC5603NJ datasheet from MEMSIC or Adafruit
   - Identify the initialization sequence
   - Identify the data output registers
   - Note the conversion formulas for magnetic field to heading

3. **Implement the driver:**
   - Set up the sensor (configure for continuous mode, set ODR)
   - Read X, Y, Z magnetic field values
   - Apply declination correction for your location
   - Calculate heading: `heading = math.atan2(y, x) * 180 / pi`
   - Normalize to 0-360 degrees

4. **Calibration:**
   - Hard iron calibration (offset correction)
   - Soft iron calibration (scaling correction)
   - Tilt compensation (if needed)

## Example I2C Implementation (Pseudocode)

```python
def init_mmc5603(i2c, address=0x30):
    # Set continuous mode
    i2c.writeto_mem(address, CONTROL_REG, [0x80])
    # Set output data rate
    i2c.writeto_mem(address, ODR_REG, [0x0A])

def read_magnetic_field(i2c, address=0x30):
    # Read 6 bytes (2 bytes each for X, Y, Z)
    data = i2c.readfrom_mem(address, DATA_REG, 6)
    
    # Combine bytes to get values
    x = (data[0] << 8) | data[1]
    y = (data[2] << 8) | data[3]
    z = (data[4] << 8) | data[5]
    
    return x, y, z

def calculate_heading(x, y, declination=0):
    # Calculate heading
    heading = math.atan2(y, x) * 180 / math.pi
    
    # Apply declination
    heading += declination
    
    # Normalize to 0-360
    if heading < 0:
        heading += 360
    elif heading >= 360:
        heading -= 360
    
    return heading
```

## Alternative Sensors

If MMC5603 is not available, consider these alternatives:
- **QMC5883L**: Similar magnetometer with CircuitPython support
- **LSM303**: Combined accelerometer + magnetometer from Adafruit
- **HMC5883L**: Older but well-supported magnetometer

## References

- MMC5603NJ Datasheet: Check MEMSIC or Adafruit product page
- Adafruit Learn Guides for similar magnetometers
- CircuitPython I2C documentation
- Magnetic declination for your location: https://www.magnetic-declination.com/
