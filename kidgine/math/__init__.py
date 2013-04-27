def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))


def interpolate(old, new, interp):
    return old * (1.0 - interp) + new * interp


def remap(value, min, max, new_min, new_max):
    return interpolate(new_min, new_max, as_percentage(value, min, max))


def as_percentage(value, min, max):
    p = value - min
    p /= (max - min)
    return p
