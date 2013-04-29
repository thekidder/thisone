import kidgine.utils
import renderable

class OpacityFader(object):
    def __init__(self, color, start, end, duration):
        self.r,self.g,self.b = color
        self.start = start
        self.end = end
        self.duration = duration
        self.time_left = duration
        self.opacity = start


    def removed(self, c):
        pass


    def update(self, t, dt, collision_detector):
        self.time_left -= dt
        self.opacity = kidgine.utils.lerp(
            (self.duration - self.time_left) / self.duration,
            self.start,
            self.end)


    def alive(self):
        return self.time_left >= 0


    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.OpacityFaderRenderable(batch, group, self)
        return wrapped


def fade_to_black(duration):
    return OpacityFader((0,0,0),0,1,duration)


def fade_from_black(duration):
    return OpacityFader((0,0,0),1,0,duration)
