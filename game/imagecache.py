import data.animations
import data.sprites


_animation_cache = dict()
_image_cache = dict()

def get_sprite(name):
    if name not in _image_cache:
        _image_cache[name] = data.sprites.get_sprite(name)

    return _image_cache[name]


def get_animation(name):
    if name not in _animation_cache:
        _animation_cache[name] = data.animations.get_animation(name)

    return _animation_cache[name]
