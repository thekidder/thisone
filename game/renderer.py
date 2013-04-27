import logging

import pyglet.graphics
from pyglet.gl import *
import character
import kidgine.math.vector
import kidgine.renderer.camera


logger = logging.getLogger(__name__)

class Renderer(object):
    def __init__(self, game):
        glClearColor(1.0, 1.0, 1.0, 1.0)

        self._game = game
        self.keystate = pyglet.window.key.KeyStateHandler()
        self.batch = pyglet.graphics.Batch()

        def camera_anchor():
            return self.player_character.position
        self.camera = kidgine.renderer.camera.CenteredCamera(camera_anchor, kidgine.math.vector.Vector(1, 1))

        self.characters = set()
        self.level = None


    def draw(self, window):
        for i in self.characters:
            i.update()

        self.camera.apply()

        if self.level:
            self.level.draw()

        self.batch.draw()


    def on_resize(self, width, height):
        ratio = 1. * height / width
        camera_size = 400

        self.camera.world_size  = kidgine.math.vector.Vector(camera_size, camera_size * ratio)
        self.camera.window_size = kidgine.math.vector.Vector(width, height)


    def set_level(self, l):
        self.level = l


    def add_character(self, c):
        if len(self.characters) == 0:
            self.player_character = c
        self.characters.add(character.CharacterRenderable(self.batch, c, c.get_sprite_name()))


    def remove_character(self, character):
        c = self.characters[character]
        c.delete()
        self.characters.remove(character)


    def on_key_press(self, symbol, modifiers):
        return self.keystate.on_key_press(symbol, modifiers)


    def on_key_release(self, symbol, modifiers):
        return self.keystate.on_key_release(symbol, modifiers)
