# Preamp Board Firmware Changelog

## 1.4

  - Upgrade fan control to PWM for Power Board Rev 3 and Power Board Rev 4
    to utilize their new digital potentiometer for linear voltage fan
    control. The three different power board revisions are auto-detected so
    that the proper control method is chosen among MAX6644, PWM, or Linear.
  - Add PI_TEMP register: the Pi will send it's temperature here so that
    it can be incorporated into the can control loop.
  - Add FAN_DUTY and FAN_VOLTS registers.
  - Upgrade the internal I2C bus speed to 400kHz.

## 1.3-93E8828

  - Move fan control from dedicated MAX6644 fan control IC to the STM32.
    The proper fan control method is auto-detected based on the presence
    of new thermocouples on the Amplifier Board.
  - Make all registers readable.
  - Make handling of internal I2C bus for each unit asyncronous to
    the controller's I2C bus. This is a step in the direction of removing
    clock stretching since the Pi doesn't support it properly, plus was
    required for the new fan control loop.
  - Update voltages and temperatures to be reported in fixed-point volts and
    degrees C, respectively.
  - Fix the controller-bus I2C address to be updatable at any time,
    not just after a reset.
  - Removed auto-baud detection until issues can be resolved.
    UART2 will operate at a fixed 9600 baud.

## 1.2-1542439

  - Save 1ms per unit at startup by resetting expansion units during
    self-initialization instead of after.
  - Add register to control expander NRST and BOOT0,
    and allow UART passthrough
  - Add UART1 (Pi<->preamp UART) auto-baud detection.
    Whatever baud is detected on UART1 is set on UART2 so that
    all UARTs in the system will talk at the same rate.
  - Upgrade internal I2C bus speed to 100 kHz, it was improperly
    set to 16.7 kHz previously.
  - Improve control I2C bus register read handling.

## 1.1-F46612D

  - Initial release
