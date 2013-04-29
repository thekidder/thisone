def scene_action(scene, method, *args, **kwargs):
    def wrapped(inputs, t, dt, collision_detector):
        getattr(scene,method)(*args, **kwargs)

    return wrapped
