def time_trigger(elapsed_time):
    def wrapped(inputs, t, dt, collision_detector):
        return t > elapsed_time

    return wrapped
