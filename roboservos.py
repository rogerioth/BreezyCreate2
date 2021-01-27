#!/usr/bin/env python3

import time
import math
import smbus
import sys
import queue
import threading

# ============================================================================
# Raspi PCA9685 16-Channel PWM Servo Driver
# ============================================================================

class PCA9685:

  # Registers/etc.
  __SUBADR1            = 0x02
  __SUBADR2            = 0x03
  __SUBADR3            = 0x04
  __MODE1              = 0x00
  __PRESCALE           = 0xFE
  __LED0_ON_L          = 0x06
  __LED0_ON_H          = 0x07
  __LED0_OFF_L         = 0x08
  __LED0_OFF_H         = 0x09
  __ALLLED_ON_L        = 0xFA
  __ALLLED_ON_H        = 0xFB
  __ALLLED_OFF_L       = 0xFC
  __ALLLED_OFF_H       = 0xFD

  def __init__(self, address=0x40, debug=False):
    self.bus = smbus.SMBus(1)
    self.address = address
    self.debug = debug
    if (self.debug):
      print("Reseting PCA9685")
    self.write(self.__MODE1, 0x00)

  def write(self, reg, value):
    "Writes an 8-bit value to the specified register/address"
    self.bus.write_byte_data(self.address, reg, value)
    if (self.debug):
      print("I2C: Write 0x%02X to register 0x%02X" % (value, reg))
          
  def read(self, reg):
    "Read an unsigned byte from the I2C device"
    result = self.bus.read_byte_data(self.address, reg)
    if (self.debug):
      print("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" % (self.address, result & 0xFF, reg))
    return result

  def setPWMFreq(self, freq):
    "Sets the PWM frequency"
    prescaleval = 25000000.0    # 25MHz
    prescaleval /= 4096.0       # 12-bit
    prescaleval /= float(freq)
    prescaleval -= 1.0
    if (self.debug):
      print("Setting PWM frequency to %d Hz" % freq)
      print("Estimated pre-scale: %d" % prescaleval)
    prescale = math.floor(prescaleval + 0.5)
    if (self.debug):
      print("Final pre-scale: %d" % prescale)

    oldmode = self.read(self.__MODE1);
    newmode = (oldmode & 0x7F) | 0x10        # sleep
    self.write(self.__MODE1, newmode)        # go to sleep
    self.write(self.__PRESCALE, int(math.floor(prescale)))
    self.write(self.__MODE1, oldmode)
    time.sleep(0.005)
    self.write(self.__MODE1, oldmode | 0x80)

  def setPWM(self, channel, on, off):
    "Sets a single PWM channel"
    self.write(self.__LED0_ON_L+4*channel, on & 0xFF)
    self.write(self.__LED0_ON_H+4*channel, on >> 8)
    self.write(self.__LED0_OFF_L+4*channel, off & 0xFF)
    self.write(self.__LED0_OFF_H+4*channel, off >> 8)
    if (self.debug):
      print("channel: %d  LED_ON: %d LED_OFF: %d" % (channel,on,off))
          
  def setServoPulse(self, channel, pulse):
    "Sets the Servo Pulse,The PWM frequency must be 50HZ"
    pulse = pulse*4096/20000        #PWM frequency is 50HZ,the period is 20000us
    self.setPWM(channel, 0, int(pulse))

  def allServos(self, pulse):
    for i in range(0, 15):
        pwm.setServoPulse(i, pulse)


class Servo:

  __SERVO_STEP         = 10

  def __init__(self, servo_id, range_max, range_min, name, default_value, controller):
    self.range_max = range_max
    self.range_min = range_min
    self.servo_id = servo_id
    self.name = name
    self.default_value = default_value
    self.currentValue = default_value
    self.controller = controller
  
  def servoOffset(self, offset):
    previewValue = self.currentValue + offset
    if previewValue > self.range_max:
      self.currentValue = self.range_max
    elif previewValue < self.range_min:
      self.currentValue = self.range_min
    else:
      self.currentValue = previewValue

  def syncServoValue(self):
    self.controller.pwm.setServoPulse(self.servo_id, self.currentValue)
  
  def servoTestRange(self):
    print(f"Performing servo test on {self.name} - Channel {self.servo_id} - Max: {self.range_max} - Min: {self.range_min}")

    for i in range(self.range_min, self.range_max, self.__SERVO_STEP):
      self.controller.pwm.setServoPulse(self.servo_id, i)
      time.sleep(0.02)
    
    for i in range(self.range_max, self.range_min, -self.__SERVO_STEP):
      self.controller.pwm.setServoPulse(self.servo_id, i)
      time.sleep(0.02)
    
    self.currentValue = self.default_value
    self.syncServoValue()

class ServoController:
  def __init__(self):
    self.pwm = PCA9685(0x40, debug=False)
    self.pwm.setPWMFreq(50)
    # create all motors

    self.base_v_angle    = Servo(13, 2280,  570, "base_v_angle", 1660, controller=self)    # ok
    self.arm_v_angle     = Servo(12, 1510,  530, "arm_v_angle",  1010, controller=self)    # ok

    self.base_rotation   = Servo( 0, 2210,  520, "base_rotation", 870, controller=self)    # ok
    self.claw            = Servo( 1, 1460, 1020, "claw", 1260, controller=self)            # ok

    self.camera_turret_v = Servo( 7, 2490, 1340, "camera_turret_v", 2280, controller=self) # ok
    self.camera_turret_h = Servo( 6, 2410,  620, "camera_turret_h", 1440, controller=self) # ok

    self.claw_angle      = Servo(15, 2180,  710, "claw_angle", 1520, controller=self)      # ok
    self.claw_rotation   = Servo(14, 2240,  510, "claw_rotation", 1220, controller=self)   # ok

    self.allMotors = [ self.base_v_angle,
                       self.arm_v_angle,
                       self.base_rotation,
                       self.claw,
                       self.camera_turret_v,
                       self.camera_turret_h,
                       self.claw_angle,
                       self.claw_rotation
                     ]

    for servo in self.allMotors:
      servo.syncServoValue()
      time.sleep(1)

    for servo in self.allMotors:
      servo.servoTestRange()
      time.sleep(0.5)

if __name__=='__main__':
    # # test args: servoId, max, min
    # print(sys.argv)
    # servoId = int(sys.argv[1])
    # servoMax = int(sys.argv[2])
    # servoMin = int(sys.argv[3])
    controller = ServoController()

#   pwm = PCA9685(0x40, debug=False)
#   pwm.setPWMFreq(50)
#   while True:
#    # setServoPulse(2,2500)
#     for i in range(500,2500,10):  
#       #pwm.setServoPulse(0,i)   
#       pwm.allServos(i)
#       time.sleep(0.02)     
    
#     for i in range(2500,500,-10):
#       #pwm.setServoPulse(0,i) 
#       pwm.allServos(i)
#       time.sleep(0.02)  
