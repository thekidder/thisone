import logging

import pyglet.graphics
from pyglet.gl import *

import character
import kidgine.math.vector
import kidgine.renderer.camera
import kidgine.renderer.utils


logger = logging.getLogger(__name__)

class SceneRenderer(object):
    def __init__(self, level):
        glClearColor(1.0, 1.0, 1.0, 1.0)

        self.keystate = pyglet.window.key.KeyStateHandler()

        self.level = level
        self.batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()
        self.player_character = None

        def camera_anchor():
            if self.player_character is None:
                return kidgine.math.vector.Vector(32*10, 32*10)
            return self.player_character.position
        self.camera = kidgine.renderer.camera.CenteredCamera(camera_anchor, kidgine.math.vector.Vector(1, 1))

        self.renderables = dict()
        self.ui_renderables = dict()


    def draw(self, t, dt, window):
        for i in self.renderables.itervalues():
            i.update(t, dt)

        self.camera.apply()

        if self.level:
            self.level.draw()

        self.batch.draw()

        for i in self.ui_renderables.itervalues():
            i.update(t, dt, window)

        kidgine.renderer.utils.screen_projection(window)
        self.ui_batch.draw()


    def on_resize(self, width, height):
        ratio = 1. * height / width
        camera_size = 400

        self.camera.world_size  = kidgine.math.vector.Vector(camera_size, camera_size * ratio)
        self.camera.window_size = kidgine.math.vector.Vector(width, height)


    def add_renderable(self, d):
        if len(self.renderables) == 0:
            self.player_character = d
        self.renderables[d] = d.create_renderable()(self.batch)


    def remove_renderable(self, object):
        r = self.renderables[object]
        r.delete()
        del self.renderables[object]


    def add_ui_renderable(self, d):
        self.ui_renderables[d] = d.create_renderable()(self.ui_batch)


    def remove_ui_renderable(self, object):
        r = self.ui_renderables[object]
        r.delete()
        del self.ui_renderables[object]


    def on_key_press(self, symbol, modifiers):
        return self.keystate.on_key_press(symbol, modifiers)


    def on_key_release(self, symbol, modifiers):
        return self.keystate.on_key_release(symbol, modifiers)
