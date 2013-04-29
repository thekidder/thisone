def action(obj, method, *args, **kwargs):
    def wrapped(inputs, t, dt, collision_detector):
        getattr(obj,method)(*args, **kwargs)

    return wrapped


def action_list(all):
    def wrapped(inputs, t, dt, collision_detector):
        for a in all:
            a(inputs, t, dt, collision_detector)

    return wrapped
