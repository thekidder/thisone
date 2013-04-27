import character
import pyglet.clock

import inputs
import kidgine.math.vector
import kidgine.renderer
import kidgine.resource
import renderer
import level


class Game(object):
    FRAME_TIME = 1/60.

    def __init__(self, configs):
        pyglet.clock.schedule_interval(self.frame, self.FRAME_TIME)
        self._inputs = inputs.Inputs()
        self._accumulator = 0.0

        icon_path = 'data/images/icon.png'
        file = pyglet.resource.file(icon_path)
        icon = pyglet.image.load(icon_path, file, decoder=pyglet.image.codecs.pil.PILImageDecoder())

        self._renderer = kidgine.renderer.Renderer(configs, 'This One', icon)
        self._gamerenderer = renderer.Renderer(self)
        self._renderer.add_drawable(0, self._gamerenderer)

        self.character = character.GirlCharacter()
        self.level = level.Level('data/levels/test.json')

        self._gamerenderer.add_character(self.character)
        self._gamerenderer.set_level(self.level)


    def frame(self, dt):
        self._accumulator += dt

        while self._accumulator > self.FRAME_TIME:
            self._inputs.update(self._gamerenderer.keystate)
            self.update(self.FRAME_TIME, self._inputs)
            self._accumulator -= self.FRAME_TIME

        self._renderer.on_draw()


    def update(self, dt, inputs):
        velocity = kidgine.math.vector.Vector(inputs.leftright * dt * 100, inputs.updown * dt * 100)
        self.character.move(velocity)
