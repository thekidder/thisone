import logging
import random

import game
import character
import inputs
import kidgine.collision
import level
import renderer
import kidgine.math.vector
from kidgine.math.vector import Vector
from collision import Tags
import dialog
import updatable


logger = logging.getLogger(__name__)

class Scene(object):
    def __init__(self, level_name):
        self._collision_detector = kidgine.collision.CollisionDetector()
        self.drawable = renderer.SceneRenderer()
        self._inputs = inputs.Inputs()

        self.updatables = set()
        self.preemptible = None

        self.level = level.Level(level_name, self._collision_detector)

        self.add_updatable(self.level)


    def update(self, t, dt):
        #self._collision_detector.log_stats(logging.INFO)
        self._inputs.update(self.drawable.keystate)
        self._collision_detector.start_frame()

        if self.preemptible is not None:
            self.preemptible.update(self._inputs, t, dt, self._collision_detector)
            if not self.preemptible.alive():
                self.preemptible.removed(self._collision_detector)
                self.drawable.remove_renderable(self.preemptible)
                self.preemptible = None
            return

        # calculate collision forces
        all = self._collision_detector.all_collisions()
        for c in all:
            if Tags.MOVEABLE not in c.shape1.tags or Tags.MOVEABLE not in c.shape2.tags:
                continue

            c.shape1.owner.collides(t, c.shape2)
            c.shape2.owner.collides(t, c.shape1)

            force = c.translation_vector * 0.4

            self._add_force(c.shape1.owner, c.shape1.tags, force)
            self._add_force(c.shape2.owner, c.shape2.tags, -force)

        # run all updatables
        all_new_objs = list()
        for obj in self.updatables:
            new_things = obj.update(self._inputs, t, dt, self._collision_detector)
            if new_things is not None:
                all_new_objs.extend(new_things)

        # add new things
        for o in all_new_objs:
            self.add_updatable(o)

        # remove dead things
        to_remove = list()
        for obj in self.updatables:
            if not obj.alive():
                to_remove.append(obj)

        for obj in to_remove:
            if obj == self.player_character:
                self.player_character = None

            self.remove_updatable(obj)


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


    def remove_updatable(self, c):
        c.removed(self._collision_detector)
        self.updatables.remove(c)
        self.drawable.remove_renderable(c)


    def add_updatable(self, c):
        self.updatables.add(c)
        self.drawable.add_renderable(c)


    def spawn_wave(self, position, enemy_type, num_enemies):
        for i in xrange(num_enemies):
            enemy = enemy_type(self.player_character, self._collision_detector)
            enemy.position = position + Vector(random.uniform(-128,128), random.uniform(-128,128))
            self.add_updatable(enemy)


    def run_preemptible(self, preemptible):
        self.drawable.add_renderable(preemptible)
        self.preemptible = preemptible


    def end_with(self, preemptible):
        pass


class ActOne(Scene):
    def __init__(self):
        super(ActOne, self).__init__('data/levels/act_one.json')
        self.player_character = character.GirlCharacter(self._inputs, self._collision_detector)
        self.player_character.position = Vector(32 * 10, 32 * 60)
        self.add_updatable(self.player_character)

        self.last_position = self.player_character.position
        self.fader = None
        self.success = False

        def camera_anchor():
            if self.player_character is None:
                return Vector(32*11, self.last_position.y)
            self.last_position = self.player_character.position
            return Vector(32 * 11, self.player_character.position.y)
        c = kidgine.renderer.camera.CenteredCamera(camera_anchor, kidgine.math.vector.Vector(32*20, 1))
        self.drawable.set_camera(c)

        self.spawn_wave(Vector(10 * 32, 40 * 32), character.MeleeEnemy, 6)

        self.add_updatable(dialog.Dialog('data/dialog/act_one_warlord_1.json'))

        self.add_updatable(updatable.fade_from_black(1.0))


    def update(self, t, dt):
        if self.player_character is None and not self.fader:
            self.fader = updatable.fade_to_black(1.5)
            self.add_updatable(self.fader)

        super(ActOne, self).update(t, dt)

        if self.fader and not self.fader.alive():
            if self.success:
                return game.SceneState.succeeded
            else:
                return game.SceneState.failed

        return game.SceneState.in_progress


class Cutscene(object):
    pass
