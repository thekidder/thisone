import logging

import character
import inputs
import kidgine.collision
import level
import renderer
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

class Scene(object):
    def __init__(self, level_name):
        self._collision_detector = kidgine.collision.CollisionDetector()
        self.level,self.level_renderable = level.load(level_name, self._collision_detector)
        self.drawable = renderer.SceneRenderer(self.level_renderable)

        self.updatables = list()


    def update(self, t, dt):
        #self._collision_detector.log_stats(logging.INFO)
        self._collision_detector.start_frame()
        for obj in self.updatables:
            obj.update(t, dt, self._collision_detector)


    def add_character(self, c):
        self.updatables.append(c)
        self.drawable.add_character(c)


class CombatScene(Scene):
    def __init__(self, level_name):
        super(CombatScene, self).__init__(level_name)

        self._inputs = inputs.Inputs()

        player_character = character.GirlCharacter(self._inputs, self._collision_detector)
        player_character.position = Vector(32 * 10, 32 * 10)

        self.add_character(player_character)

        for i in xrange(5):
            enemy = character.MeleeEnemy(player_character, self._collision_detector)
            enemy.position = Vector(32 * (4 + i), 32 * (4 + i))
            self.add_character(enemy)



    def update(self, t, dt):
        self._inputs.update(self.drawable.keystate)
        super(CombatScene, self).update(t, dt)


class Cutscene(object):
    pass
