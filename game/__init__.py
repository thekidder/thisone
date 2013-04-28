import pyglet.clock

import kidgine.math.vector
import kidgine.renderer
import scene
import debug


class Game(object):
    FRAME_TIME = 1/60.

    def __init__(self, configs):
        pyglet.clock.schedule_interval(self.frame, self.FRAME_TIME)
        self._accumulator = 0.0
        self._gametime = 0.0
        self.scene = None

        icon_path = 'data/images/icon.png'
        file = pyglet.resource.file(icon_path)
        icon = pyglet.image.load(icon_path, file, decoder=pyglet.image.codecs.pil.PILImageDecoder())

        self._renderer = kidgine.renderer.Renderer(configs, 'This One', icon)
        self._renderer.add_drawable(20, debug.DebugOverlay())

        self.set_scene(scene.CombatScene('data/levels/test.json'))


    def frame(self, dt):
        self._accumulator += dt

        while self._accumulator > self.FRAME_TIME:
            self.update(self._gametime, self.FRAME_TIME)
            self._accumulator -= self.FRAME_TIME
            self._gametime += self.FRAME_TIME

        self._renderer.on_draw(self._gametime, self.FRAME_TIME)


    def update(self, t, dt):
        if self.scene is not None:
            self.scene.update(t, dt)


    def set_scene(self, scene):
        if self.scene is not None:
            self._renderer.remove_drawable(self.scene.drawable)
        self.scene = scene
        self._renderer.add_drawable(10, self.scene.drawable)
