import logging
import sys

import pyglet.clock

import character
import kidgine.math.vector
import kidgine.renderer
import kidgine.utils
import scene
import debug


SceneState = kidgine.utils.enum('in_progress','failed','succeeded')

logger = logging.getLogger(__name__)

class Game(object):
    FRAME_TIME = 1/60.

    def __init__(self, scene_index, easy_mode, configs):
        if easy_mode:
            character.health_scaling = 0.1

        pyglet.clock.schedule_interval(self.frame, self.FRAME_TIME)
        self._accumulator = 0.0
        self._gametime = 0.0
        self.scene = None

        icon_path = 'data/images/icon.png'
        file = pyglet.resource.file(icon_path)
        icon = pyglet.image.load(icon_path, file, decoder=pyglet.image.codecs.pil.PILImageDecoder())

        self._renderer = kidgine.renderer.Renderer(configs, 'This One', icon)
        #self._renderer.add_drawable(20, debug.DebugOverlay())

        self.scene_list = [scene.Title, scene.ActOne, scene.ActTwo, scene.ActThree]
        self.current_scene = scene_index

        self.set_scene(self.scene_list[self.current_scene]())


    def frame(self, dt):
        self._accumulator += dt

        while self._accumulator > self.FRAME_TIME:
            state = self.update(self._gametime, self.FRAME_TIME)
            if state != SceneState.in_progress:
                self.check_state(state)
                return
            self._accumulator -= self.FRAME_TIME
            self._gametime += self.FRAME_TIME

        self._renderer.on_draw(self._gametime, self.FRAME_TIME)


    def check_state(self, state):
        if state == SceneState.succeeded:
            logger.info('completed scene {}, moving on'.format(self.current_scene))
            self.current_scene += 1
        else:
            logger.info('failed scene {}, restarting'.format(self.current_scene))

        if self.current_scene == len(self.scene_list):
            logger.info('you beat the game!')
            sys.exit(0)

        self.set_scene(self.scene_list[self.current_scene]())


    def update(self, t, dt):
        if self.scene is not None:
            return self.scene.update(t, dt)


    def set_scene(self, scene):
        self._gametime = 0
        self._accumulator = 0

        if self.scene is not None:
            self._renderer.remove_drawable(self.scene.drawable)
        self.scene = scene
        self._renderer.add_drawable(10, self.scene.drawable)

        # make sure we get an update
        self.update(self._gametime, self.FRAME_TIME)
        self._accumulator -= self.FRAME_TIME
        self._gametime += self.FRAME_TIME
