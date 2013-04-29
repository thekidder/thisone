import logging

import pyglet.graphics
from pyglet.gl import *

import character
import kidgine.math.vector
import kidgine.renderer.camera
import kidgine.renderer.utils
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

class SceneRenderer(object):
    def __init__(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_BLEND)

        self.keystate = pyglet.window.key.KeyStateHandler()

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
        if obj.is_ui():
            renderable = obj.create_renderable()(self.ui_batch, self.ui_group)
            self.ui_renderables[obj] = renderable
        else:
            renderable = obj.create_renderable()(self.batch, self.group)
            self.renderables[obj] = renderable


    def remove_renderable(self, obj):
        if obj.is_ui():
            r = self.ui_renderables[obj]
            r.delete()
            del self.ui_renderables[obj]
        else:
            r = self.renderables[obj]
            r.delete()
            del self.renderables[obj]


    def on_key_press(self, symbol, modifiers):
        return self.keystate.on_key_press(symbol, modifiers)


    def on_key_release(self, symbol, modifiers):
        return self.keystate.on_key_release(symbol, modifiers)
