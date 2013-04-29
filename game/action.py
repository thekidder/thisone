import updatable


def action(obj, method, *args, **kwargs):
    def wrapped(inputs, t, dt, collision_detector):
        return getattr(obj,method)(*args, **kwargs)

    return wrapped


def action_list(all):
    def wrapped(inputs, t, dt, collision_detector):
        returned_list = list()
        for a in all:
            new_entities = a(inputs, t, dt, collision_detector)
            if new_entities:
                returned_list.extend(new_entities)
        return returned_list

    return wrapped


def add_updatable(updatable):
    def wrapped(inputs, t, dt, collision_detector):
        return [updatable]

    return wrapped


def add_trigger(scene, trigger, action):
    def wrapped(inputs, t, dt, collision_detector):
        t = updatable.TriggeredUpdatable(trigger, action)
        scene._triggers[trigger] = t
        return [t]

    return wrapped
