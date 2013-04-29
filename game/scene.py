import logging
import random

import game
import camera
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

        self.return_state = None

        self.level = level.Level(level_name, self._collision_detector)

        self.add_updatable(self.level)



    def update(self, t, dt):
        #self._collision_detector.log_stats(logging.INFO)
        self._inputs.update(self.drawable.keystate)
        self._collision_detector.start_frame()

        if self.preemptible is not None:
            self.preemptible.update(self._inputs, t, dt, self._collision_detector)
            if not self.preemptible.alive():
                self.remove_preemptible()

                if self.return_state:
                    return self.return_state
            return game.SceneState.in_progress

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

        return game.SceneState.in_progress


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


    #
    # Subclass API starts here
    #

    def remove_updatable(self, c):
        c.removed(self._collision_detector)
        self.updatables.remove(c)
        self.drawable.remove_renderable(c)


    def add_updatable(self, c):
        self.updatables.add(c)
        self.drawable.add_renderable(c)


    def run_preemptible(self, preemptible):
        self.remove_preemptible()
        self.drawable.add_renderable(preemptible)
        self.preemptible = preemptible


    def remove_preemptible(self):
        if self.preemptible is not None:
            self.preemptible.removed(self._collision_detector)
            self.drawable.remove_renderable(self.preemptible)
            self.preemptible = None


    def end_with(self, state, preemptible):
        if self.return_state is None:
            self.return_state = state
            self.run_preemptible(preemptible)


    def set_camera(self, cam):
        self.drawable.set_camera(cam)


    def spawn_wave(self, position, enemy_type, num_enemies):
        for i in xrange(num_enemies):
            p = position + Vector(random.uniform(-128,128), random.uniform(-128,128))
            enemy = enemy_type(p, self.player_character)
            self.add_updatable(enemy)


class ActOne(Scene):
    def __init__(self):
        super(ActOne, self).__init__('data/levels/act_one.json')

        self.player_character = character.GirlCharacter(Vector(32 * 10, 32 * 60))
        self.add_updatable(self.player_character)

        self.set_camera(camera.VerticalPanningCamera(self.player_character, 32 * 11, 32 * 20))

        self.spawn_wave(Vector(10 * 32, 40 * 32), character.MeleeEnemy, 6)

        #self.add_updatable(dialog.Dialog('data/dialog/act_one_warlord_1.json'))

        self.add_updatable(updatable.fade_from_black(1.0))


    def update(self, t, dt):
        if self.player_character is None:
            self.end_with(game.SceneState.failed, updatable.fade_to_black(1.5))

        return super(ActOne, self).update(t, dt)


class Cutscene(object):
    pass
