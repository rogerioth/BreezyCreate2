#!/usr/bin/env python3

'''
robotserver.py 

Serves a socket that accepts <X,Y,A> tuples from a client's joystick.

X,Y are control axes (-1..+1); A is autopilot flag (0 or 1).

This code is part of BreezyCreate2

The MIT License

Copyright (c) 2016 Simon D. Levy, Rajwol Joshi, Jamie White, Logan Wilson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

from breezycreate2 import Robot
from time import sleep
import socket
import threading
import RPi.GPIO as GPIO

# These are sensible values for  RaspberryPi ad-hoc network
HOST        = '192.168.87.32'
PORT        = 20000
BUFSIZE     = 100
servoPIN_X  = 17
servoPIN_Y  = 18
PX_MAX      = 12.8
PX_MIN      = 0.3
PY_MAX      = 12
PY_MIN      = 7

px_duty     = 2.5
py_duty     = 12

MOTOR_MAX_SPEED = 400

GPIO.setmode(GPIO.BCM)
GPIO.setup(servoPIN_X, GPIO.OUT)
GPIO.setup(servoPIN_Y, GPIO.OUT)
px = GPIO.PWM(servoPIN_X, 50) # GPIO 17 for PWM with 50Hz
px.start(px_duty) # Initialization
py = GPIO.PWM(servoPIN_Y, 50) # GPIO 18 for PWM with 50Hz
py.start(py_duty) # Initialization

def attemptOffset(isX, offset):
    global px_duty
    global py_duty

    if isX:
        predicted_x = px_duty + offset
        if predicted_x > PX_MAX:
            px_duty = PX_MAX
        elif predicted_x < PX_MIN:
            px_duty = PX_MIN
        else:
            px_duty = predicted_x
    else:
        predicted_y = py_duty + offset
        if predicted_y > PY_MAX:
            py_duty = PY_MAX
        elif predicted_y < PY_MIN:
            py_duty = PY_MIN
        else:
            py_duty = predicted_y


def handleTurret(turret_offset_x, turret_offset_y):
    global px_duty
    global py_duty

    attemptOffset(True,  (turret_offset_x / 10))
    attemptOffset(False, (turret_offset_y / 10))
    print('Turret - X:' + str(px_duty) + '; Y: ' + str(py_duty))

    px.ChangeDutyCycle(px_duty)
    py.ChangeDutyCycle(py_duty)
    sleep(0.05)

def threadfunc(values):

    # Connect to the Create2
    bot = Robot()
    
    while True:

        #Convert [-1,+1] axis to [-500,+500] turn speed
        if abs(values[0]) > abs(values[1]):
            # Only turn
            bot.setTurnSpeed(MOTOR_MAX_SPEED*values[0])
        else:
            bot.setForwardSpeed(MOTOR_MAX_SPEED*values[1])

        handleTurret(values[3], values[4])

        # Yield to main thread
        sleep(.01)
        
if __name__ == '__main__':

    # Listen for a client ------------------------------------------------------
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.bind((HOST, PORT)) # Note tuple!

    except socket.error as error:
       print('bind() failed on ' + HOST + ':' + str(PORT) + ' ' + str(error))
       exit(1)

    print('Waiting for a client ...')

    sock.listen(1)  # handle up to 1 back-logged connection

    client, address = sock.accept()

    print('Accepted connection')

    # These values will be shared with the command-listener thread
    values = [0,0,0,0,0]

    # Launch command listener on another thread
    thread = threading.Thread(target=threadfunc, args = (values,))
    thread.daemon = True
    thread.start()

    # Loop forever, getting <X,Y,A> tuples from the client and sharing them with
    # the command listener
    while True:

        msg = ''

        messages = client.recv(BUFSIZE).decode().split('*')
        for message in messages:
            parts = message.split()
            if len(parts) == 5:
                values[0] = float(parts[0])
                values[1] = float(parts[1])
                values[2] = int(parts[2])
                values[3] = float(parts[3])
                values[4] = float(parts[4])
