import logging

import pyglet.graphics
import pyglet.media
import pyglet.sprite

import kidgine.math.vector
import kidgine.renderer.camera
import sprites


logger = logging.getLogger(__name__)

class Renderer(object):
    def __init__(self, game):
        self._game = game
        self.keystate = pyglet.window.key.KeyStateHandler()
        self.batch = pyglet.graphics.Batch()

        def camera_anchor():
            return kidgine.math.vector.constant_zero
        self.camera = kidgine.renderer.camera.CenteredCamera(camera_anchor, kidgine.math.vector.Vector(1, 1))


    def draw(self, window):
        self.camera.apply()
        self.batch.draw()


    def on_resize(self, width, height):
        ratio = 1. * height / width
        camera_size = 400

        self.camera.world_size  = kidgine.math.vector.Vector(camera_size, camera_size * ratio)
        self.camera.window_size = kidgine.math.vector.Vector(width, height)


    def on_key_press(self, symbol, modifiers):
        return self.keystate.on_key_press(symbol, modifiers)


    def on_key_release(self, symbol, modifiers):
        return self.keystate.on_key_release(symbol, modifiers)
