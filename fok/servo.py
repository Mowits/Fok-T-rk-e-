import time


class _NoopServo:
    def update(self, _target_x_norm: float):
        return

    def close(self):
        return


def try_init_servo_tracker(cfg: dict):
    if not cfg.get("servo_tracking_enabled", False):
        return _NoopServo()
    try:
        import RPi.GPIO as GPIO
    except Exception:
        return _NoopServo()

    pin = int(cfg.get("servo_pin", 18))
    freq = int(cfg.get("servo_freq", 50))
    center = float(cfg.get("servo_center_deg", 90))
    min_deg = float(cfg.get("servo_min_deg", 20))
    max_deg = float(cfg.get("servo_max_deg", 160))
    step = float(cfg.get("servo_step_deg", 3))
    deadband = float(cfg.get("servo_deadband", 0.08))
    settle = float(cfg.get("servo_settle_sec", 0.02))

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT)
    pwm = GPIO.PWM(pin, freq)
    pwm.start(0.0)

    state = {"deg": max(min(center, max_deg), min_deg), "last": 0.0}

    def _deg_to_dc(deg: float) -> float:
        # SG90 typical mapping: 0-180deg => 2.5-12.5 duty at 50Hz
        return 2.5 + (deg / 180.0) * 10.0

    def _write(deg: float):
        dc = _deg_to_dc(deg)
        pwm.ChangeDutyCycle(dc)
        time.sleep(settle)
        pwm.ChangeDutyCycle(0.0)

    _write(state["deg"])

    class Tracker:
        def update(self, target_x_norm: float):
            now = time.time()
            if now - state["last"] < 0.05:
                return
            state["last"] = now

            err = float(target_x_norm) - 0.5
            if abs(err) < deadband:
                return

            # target image center is 0.5; servo direction may need inversion on rig
            if err > 0:
                state["deg"] -= step
            else:
                state["deg"] += step
            state["deg"] = max(min_deg, min(max_deg, state["deg"]))
            _write(state["deg"])

        def close(self):
            try:
                pwm.stop()
            finally:
                GPIO.cleanup(pin)

    return Tracker()
