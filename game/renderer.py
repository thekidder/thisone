import logging

import pyglet.graphics
from pyglet.gl import *

import character
import kidgine.math.vector
import kidgine.renderer.camera
import kidgine.renderer.utils
from kidgine.math.vector import Vector
import updatable


logger = logging.getLogger(__name__)

class SceneRenderer(object):
    def __init__(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_BLEND)

        self.keystate = pyglet.window.key.KeyStateHandler()

        self.level_batch = pyglet.graphics.Batch()
        self.batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()

        self.group = pyglet.graphics.NullGroup()
        self.ui_group = pyglet.graphics.NullGroup()

        self.renderables = dict()
        self.ui_renderables = dict()

        self.camera = None
        self.width = 1.
        self.height = 1.


    def draw(self, t, dt, window):
        for i in self.renderables.itervalues():
            i.update(t, dt)

        self.camera.apply()

        self.level_batch.draw()
        self.batch.draw()

        for i in self.ui_renderables.itervalues():
            i.update(t, dt, window)

        kidgine.renderer.utils.screen_projection(window)
        self.ui_batch.draw()


    def set_camera(self, cam):
        self.camera = cam
        self.on_resize(self.width,self.height)


    def on_resize(self, width, height):
        self.width = width
        self.height = height

        ratio = 1. * height / width

        if self.camera:
            self.camera.world_size  = kidgine.math.vector.Vector(self.camera.world_size.x,
                                                                 self.camera.world_size.x * ratio)
            self.camera.window_size = kidgine.math.vector.Vector(width, height)


    def add_renderable(self, obj):
        type = obj.create_renderable()
        if not type:
            return

        if obj.is_ui():
            renderable = type(self.ui_batch, self.ui_group)
            self.ui_renderables[obj] = renderable
        else:
            b = self.batch
            if updatable.Tags.level in obj.get_tags():
                b = self.level_batch

            renderable = type(self.batch, self.group)
            self.renderables[obj] = renderable


    def remove_renderable(self, obj):
        try:
            is_ui = obj.is_ui()
        except AttributeError:
            pass
        else:
            if is_ui:
                if obj in self.ui_renderables:
                    r = self.ui_renderables[obj]
                    r.delete()
                    del self.ui_renderables[obj]
            else:
                if obj in self.renderables:
                    r = self.renderables[obj]
                    r.delete()
                    del self.renderables[obj]


    def on_key_press(self, symbol, modifiers):
        return self.keystate.on_key_press(symbol, modifiers)


    def on_key_release(self, symbol, modifiers):
        return self.keystate.on_key_release(symbol, modifiers)
