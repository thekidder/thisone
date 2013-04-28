import logging

import character
import inputs
import kidgine.collision
import level
import renderer
import kidgine.math.vector
from kidgine.math.vector import Vector
from collision import Tags


logger = logging.getLogger(__name__)

class Scene(object):
    def __init__(self, level_name):
        self._collision_detector = kidgine.collision.CollisionDetector()
        self.level,self.level_renderable = level.load(level_name, self._collision_detector)
        self.drawable = renderer.SceneRenderer(self.level_renderable)

        self.updatables = set()


    def update(self, t, dt):
        #self._collision_detector.log_stats(logging.INFO)
        self._collision_detector.start_frame()

        all = self._collision_detector.all_collisions()
        for c in all:
            if Tags.MOVEABLE not in c.shape1.tags or Tags.MOVEABLE not in c.shape2.tags:
                continue

            c.shape1.owner.collides(t, c.shape2)
            c.shape2.owner.collides(t, c.shape1)

            #c1 = c.shape1.transformed_point(kidgine.math.vector.constant_zero)
            #c2 = c.shape2.transformed_point(kidgine.math.vector.constant_zero)

            #separation = c2 - c1
            #force = 1.0 / separation.magnitude_sqr() * c.translation_vector.normalized()

            force = c.translation_vector * 0.5

            #force = c.translation_vector * c.translation_vector * 0.1

            #logger.info('force v = {}'.format(force))

            self._add_force(c.shape1.owner, c.shape1.tags, force)
            self._add_force(c.shape2.owner, c.shape2.tags, -force)
            #logger.info('{} -> {}: apply {}'.format(c.shape1.owner.position,c.shape2.owner.position, force))
            #logger.info('({}, {}) with ({}, {})'.format(c.token1, c.shape1, c.token2, c.shape2))

        for obj in self.updatables:
            obj.update(t, dt, self._collision_detector)

        for obj in self.updatables:
            self._reset_force(obj)


    def _reset_force(self, obj):
        try:
            obj.reset_force()
        except AttributeError:
            pass


    def _add_force(self, obj, tags, force):
        if Tags.PLAYER in tags:
            force *= 0.2
        try:
            obj.apply_force(force)
        except AttributeError:
            pass


    def remove_character(self, c):
        self.updatables.remove(c)
        self.drawable.remove_character(c)


    def add_character(self, c):
        self.updatables.add(c)
        self.drawable.add_character(c)


class CombatScene(Scene):
    def __init__(self, level_name):
        super(CombatScene, self).__init__(level_name)

        self._inputs = inputs.Inputs()

        self.player_character = character.GirlCharacter(self._inputs, self._collision_detector)
        self.player_character.position = Vector(32 * 10, 32 * 10)

        self.add_character(self.player_character)

        for i in xrange(6):
            enemy = character.MeleeEnemy(self.player_character, self._collision_detector)
            enemy.position = Vector(32 * (1 + i), 32 * (1 + i))
            self.add_character(enemy)


    def update(self, t, dt):
        self._inputs.update(self.drawable.keystate)
        super(CombatScene, self).update(t, dt)


        if self.player_character and self.player_character.health == 0.0:
            self.remove_character(self.player_character)
            self.player_character = None


class Cutscene(object):
    pass
