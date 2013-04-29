import logging
import random

import action
import camera
import character
import game
import inputs
import kidgine.collision
import level
import renderer
import trigger
import updatable
from collision import Tags
from kidgine.math.vector import Vector


logger = logging.getLogger(__name__)

class Scene(object):
    def __init__(self, level_name):
        self._collision_detector = kidgine.collision.CollisionDetector()
        self.drawable = renderer.SceneRenderer()
        self._inputs = inputs.Inputs()

        self.updatables = set()
        self._triggers = dict()
        self.blocking_event = None

        self.player_character = None
        self.return_state = None

        self.level = level.Level(level_name, self._collision_detector)

        self.add_updatable(self.level)



    def update(self, t, dt):
        #self._collision_detector.log_stats(logging.INFO)
        self._inputs.update(self.drawable.keystate)
        self._collision_detector.start_frame()

        if self.blocking_event is not None:
            self.blocking_event.update(self._inputs, t, dt, self._collision_detector)
            if not self.blocking_event.alive():
                self.remove_blocking_event()

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

    def add_updatable(self, c):
        self.updatables.add(c)
        self.drawable.add_renderable(c)


    def remove_updatable(self, c):
        c.removed(self._collision_detector)
        self.updatables.remove(c)
        self.drawable.remove_renderable(c)


    def run_blocking_event(self, blocking_event):
        self.remove_blocking_event()
        self.drawable.add_renderable(blocking_event)
        self.blocking_event = blocking_event


    def remove_blocking_event(self):
        if self.blocking_event is not None:
            self.blocking_event.removed(self._collision_detector)
            self.drawable.remove_renderable(self.blocking_event)
            self.blocking_event = None


    def add_trigger(self, trigger, action):
        t = updatable.TriggeredUpdatable(trigger, action)
        self._triggers[trigger] = t
        self.add_updatable(t)


    def remove_trigger(self, trigger):
        del self._triggers[trigger]


    def end_with(self, state, updatable):
        if self.return_state is None:
            self.return_state = state
            self.run_blocking_event(updatable)


    def set_camera(self, cam):
        self.drawable.set_camera(cam)


    def is_player_alive(self):
        if self.player_character:
            return self.player_character.alive()
        else:
            return False


    def is_player_dead(self):
        return not self.is_player_alive()


    def spawn_wave(self, position, enemy_type, num_enemies):
        for i in xrange(num_enemies):
            p = position + Vector(random.uniform(-128,128), random.uniform(-128,128))
            enemy = enemy_type(p, self.player_character)
            self.add_updatable(enemy)


class ActOne(Scene):
    def __init__(self):
        super(ActOne, self).__init__('data/levels/act_one.json')

        # create player
        self.player_character = character.GirlCharacter(Vector(32 * 10, 32 * 60))
        self.add_updatable(self.player_character)

        # set camera
        self.set_camera(camera.VerticalPanningCamera(self.player_character, 32 * 11, 32 * 20))

        # create some enemies
        self.spawn_wave(Vector(10 * 32, 40 * 32), character.MeleeEnemy, 6)

        # start by fading from black
        self.add_updatable(updatable.fade_from_black(1.0))

        # set up some triggers

        # lose when the player dies
        self.add_trigger(trigger.trigger(self, 'is_player_dead'),
                         action.action(self, 'end_with',
                                       game.SceneState.failed,
                                       updatable.fade_to_black(0.5)))

        # play some dialog

        #self.play_dialog('data/dialog/act_one_warlord_1.json'))


class Cutscene(object):
    pass
