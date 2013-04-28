import logging

import pyglet.graphics
from pyglet.gl import *

import character
import kidgine.math.vector
import kidgine.renderer.camera


logger = logging.getLogger(__name__)

class SceneRenderer(object):
    def __init__(self, level):
        glClearColor(1.0, 1.0, 1.0, 1.0)

        self.keystate = pyglet.window.key.KeyStateHandler()

        self.level = level
        self.batch = pyglet.graphics.Batch()

        def camera_anchor():
            return self.player_character.position
        self.camera = kidgine.renderer.camera.CenteredCamera(camera_anchor, kidgine.math.vector.Vector(1, 1))

        self.characters = set()


    def draw(self, t, dt, window):
        for i in self.characters:
            i.update(t, dt)

        self.camera.apply()

        if self.level:
            self.level.draw()

        self.batch.draw()


    def on_resize(self, width, height):
        ratio = 1. * height / width
        camera_size = 400

        self.camera.world_size  = kidgine.math.vector.Vector(camera_size, camera_size * ratio)
        self.camera.window_size = kidgine.math.vector.Vector(width, height)


    def add_character(self, c):
        if len(self.characters) == 0:
            self.player_character = c
        self.characters.add(c.renderable_type()(self.batch, c))


    def remove_character(self, character):
        c = self.characters[character]
        c.delete()
        self.characters.remove(character)


    def on_key_press(self, symbol, modifiers):
        return self.keystate.on_key_press(symbol, modifiers)


    def on_key_release(self, symbol, modifiers):
        return self.keystate.on_key_release(symbol, modifiers)
