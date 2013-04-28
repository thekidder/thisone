import renderable


class Firebolt(object):
    def __init__(self, position):
        self.time_left = 0.2


    def update(self, t, dt, collision_detector):
        self.time_left -= dt


    def alive(self):
        return self.time_left > 0.0


    def create_renderable(self):
        def wrapped(batch):
            return renderable.StaticSpriteRenderable(batch, self, 'fire_peak')
        return wrapped
