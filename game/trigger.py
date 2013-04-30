def time_trigger(elapsed_time):
    def wrapped(inputs, t, dt, collision_detector):
        return t > elapsed_time

    return wrapped


def trigger(obj, method, *args, **kwargs):
    def wrapped(inputs, t, dt, collision_detector):
        return getattr(obj,method)(*args, **kwargs)

    return wrapped


def key_pressed(inputs, t, dt, c):
    return inputs.dialog_dismiss
