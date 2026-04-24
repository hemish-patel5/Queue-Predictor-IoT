#!/usr/bin/env python3
import PCF8591 as ADC
import RPi.GPIO as GPIO
import time

DO = 17

GPIO.setmode(GPIO.BCM)

def setup():
    ADC.setup(0x48)
    GPIO.setup(DO, GPIO.IN)

def print_status(x):
    if x == 1:
        print('')
        print('   *********')
        print('   * Safe~ *')
        print('   *********')
        print('')
    if x == 0:
        print('')
        print('   ***************')
        print('   * Danger Gas! *')
        print('   ***************')
        print('')

def loop():
    status = 1
    while True:
        print(ADC.read(0))
        tmp = GPIO.input(DO)
        if tmp != status:
            print_status(tmp)
            status = tmp
        time.sleep(0.2)

def destroy():
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        destroy()