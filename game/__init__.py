import pyglet.clock

import inputs
import kidgine.math.vector
import kidgine.renderer
import renderer


class Game(object):
    FRAME_TIME = 1/60.

    def __init__(self, configs):
        pyglet.clock.schedule_interval(self.frame, self.FRAME_TIME)
        self._inputs = inputs.Inputs()
        self._accumulator = 0.0
        self._renderer = kidgine.renderer.Renderer(configs)
        self._gamerenderer = renderer.Renderer(self)

        self._renderer.add_drawable(0, self._gamerenderer)


    def frame(self, dt):
        self._accumulator += dt

        while self._accumulator > self.FRAME_TIME:
            self._inputs.update(self._gamerenderer.keystate)
            self.update(self.FRAME_TIME, self._inputs)
            self._accumulator -= self.FRAME_TIME

        self._renderer.on_draw()


    def update(self, dt, inputs):
        pass
