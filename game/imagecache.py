import sprites


cache = dict()

def get_sprite(name):
    if name not in cache:
        cache[name] = sprites.get_sprite(name)

    return cache[name]
