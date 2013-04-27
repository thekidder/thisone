import data.sprites


cache = dict()

def get_sprite(name):
    if name not in cache:
        cache[name] = data.sprites.get_sprite(name)

    return cache[name]
