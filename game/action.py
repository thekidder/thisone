def action(obj, method, *args, **kwargs):
    def wrapped(inputs, t, dt, collision_detector):
        getattr(obj,method)(*args, **kwargs)

    return wrapped
