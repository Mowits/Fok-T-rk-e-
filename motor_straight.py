#!/usr/bin/env python3
import argparse
import time

import RPi.GPIO as GPIO


def parse_args():
    p = argparse.ArgumentParser(description="Single direction DC motor run test (NPN + diode).")
    p.add_argument("--pin", type=int, default=18, help="BCM GPIO pin (recommended: 18)")
    p.add_argument("--duty", type=float, default=55.0, help="PWM duty cycle 0-100")
    p.add_argument("--freq", type=int, default=1000, help="PWM frequency (Hz)")
    p.add_argument("--duration", type=float, default=5.0, help="Run time in seconds")
    return p.parse_args()


def main():
    args = parse_args()
    duty = max(0.0, min(100.0, args.duty))

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(args.pin, GPIO.OUT)
    pwm = GPIO.PWM(args.pin, args.freq)

    try:
        print(f"[MOTOR] start pin={args.pin} duty={duty}% freq={args.freq}Hz duration={args.duration}s")
        pwm.start(duty)
        time.sleep(max(0.0, args.duration))
        pwm.ChangeDutyCycle(0.0)
        print("[MOTOR] stop")
    finally:
        pwm.stop()
        GPIO.cleanup(args.pin)


if __name__ == "__main__":
    main()
