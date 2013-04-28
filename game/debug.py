import pyglet.clock

import kidgine.renderer.utils


class DebugOverlay(object):
    def __init__(self):
        self._clock = pyglet.clock.ClockDisplay()


    def draw(self, t, dt, window):
        kidgine.renderer.utils.screen_projection(window)
        self._clock.draw()
