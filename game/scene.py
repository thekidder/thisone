import collections
import logging
import random

import dialog

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

        # separate game time from scene time. scene time pauses during blocking events
        self._scene_time = 0

        self.updatables = set()
        self._triggers = dict()
        self._blocking_events = collections.deque()
        self._current_blocking_event = None

        self.player_character = None
        self.return_state = None

        self.level = level.Level(level_name, self._collision_detector)

        self.add_updatable(self.level)



    def update(self, t, dt):
        #self._collision_detector.log_stats(logging.INFO)
        self._inputs.update(self.drawable.keystate)
        self._collision_detector.start_frame()

        if self._current_blocking_event is not None:
            to_add = self._current_blocking_event.update(self._inputs, t, dt, self._collision_detector)
            if not self._current_blocking_event.alive():
                if self.return_state:
                    return self.return_state

                self._remove_blocking_event()

            if to_add is not None:
                for u in to_add:
                    self.add_updatable(u)
            return game.SceneState.in_progress

        self._scene_time += dt

        # calculate collision forces
        all = self._collision_detector.all_collisions()
        for c in all:
            try:
                c.shape1.owner.collides(t, c.shape2)
            except AttributeError:
                pass
            try:
                c.shape2.owner.collides(t, c.shape1)
            except AttributeError:
                pass

            if Tags.MOVEABLE not in c.shape1.tags or Tags.MOVEABLE not in c.shape2.tags:
                continue

            force = c.translation_vector * 0.4

            self._add_force(c.shape1.owner, c.shape1.tags, force)
            self._add_force(c.shape2.owner, c.shape2.tags, -force)

        # run all updatables
        all_new_objs = list()
        for obj in self.updatables:
            new_things = obj.update(self._inputs, self._scene_time, dt, self._collision_detector)
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

    def _remove_blocking_event(self):
        if self._current_blocking_event is not None:
            self._current_blocking_event.removed(self._collision_detector)
            self.drawable.remove_renderable(self._current_blocking_event)
            if len(self._blocking_events) > 0:
                self._current_blocking_event,self.return_state = self._blocking_events.popleft()
                self.drawable.add_renderable(self._current_blocking_event)
            else:
                self._current_blocking_event = None

    #
    # Subclass API starts here
    #


    # Query Functions

    def is_player_alive(self):
        if self.player_character:
            return self.player_character.alive()
        else:
            return False


    def is_player_dead(self):
        return not self.is_player_alive()


    def all_enemies_dead(self):
        for u in self.updatables:
            if updatable.Tags.enemy in u.get_tags():
                return False
        return True

    # Actions and Setters

    def add_updatable(self, c):
        self.updatables.add(c)
        self.drawable.add_renderable(c)


    def add_updatables(self, l):
        for u in l:
            self.add_updatable(u)


    def remove_updatable(self, c):
        c.removed(self._collision_detector)
        self.updatables.remove(c)
        self.drawable.remove_renderable(c)


    def add_blocking_event(self, blocking_event, ending_state = None):
        if self._current_blocking_event is None:
            self._current_blocking_event = blocking_event
            self.drawable.add_renderable(self._current_blocking_event)
            self.return_state = ending_state
        else:
            self._blocking_events.append((blocking_event, ending_state))


    def add_trigger(self, trigger, action):
        t = updatable.TriggeredUpdatable(trigger, action)
        self._triggers[trigger] = t
        self.add_updatable(t)


    def remove_trigger(self, trigger):
        del self._triggers[trigger]


    def end_with(self, state, updatable):
        self.add_blocking_event(updatable, ending_state = state)


    def play_dialog(self, dialog_path, blocking = True):
        d = dialog.Dialog(dialog_path)
        if blocking:
            self.add_blocking_event(d)
        else:
            self.add_updatable(d)


    def set_camera(self, cam):
        self.drawable.set_camera(cam)


    def create_wave(self, position, enemy_type, num_enemies, spread):
        all = list()
        for i in xrange(num_enemies):
            p = position + Vector(random.uniform(-spread,spread), random.uniform(-spread,spread))
            enemy = enemy_type(p, self.player_character)
            all.append(enemy)

        return all


class ActOne(Scene):
    def __init__(self):
        super(ActOne, self).__init__('data/levels/act_one.json')

        # create player
        self.player_character = character.GirlCharacter(Vector(32 * 10, 32 * 3))
        self.player_character.facing = character.Facing.top
        self.add_updatable(self.player_character)

        # set camera
        self.set_camera(camera.VerticalPanningCamera(self.player_character,
                                                     32 * 11, # center x
                                                     32 * 20, # width
                                                     32 * 8)) # min_y

        # create some enemies
        self.add_updatables(self.create_wave(Vector(4 * 32, 8 * 32), character.MeleeEnemy, 2, 48))
        self.add_updatables(self.create_wave(Vector(13 * 32, 9 * 32), character.MeleeEnemy, 3, 48))


        # fade from black
        self.add_blocking_event(updatable.fade_from_black(1.0))
        # play some dialog
        self.play_dialog('data/dialog/act_one_intro.json')


        # set up some triggers

        # lose when the player dies
        self.add_trigger(
            trigger.trigger(self, 'is_player_dead'),
            action.action_list(
                [
                    action.action(self, 'play_dialog', 'data/dialog/death_dialog.json'),
                    action.action(self, 'end_with',
                                  game.SceneState.failed,
                                  updatable.fade_to_black(0.5))
                ]
            )
        )

        # enemie waves
        self.add_trigger(
            trigger.trigger(self, 'should_spawn_wave_2'),
            action.action_list(
                [
                    action.add_updatables(self.create_wave(Vector(3 * 32, 21 * 32), character.MeleeEnemy, 4, 48)),
                    action.add_updatables(self.create_wave(Vector(17 * 32, 24 * 32), character.MeleeEnemy, 3, 48))
                ]
            )
        )

        self.add_trigger(
            trigger.trigger(self, 'should_spawn_wave_3'),
            action.action_list(
                [
                    action.add_updatables(self.create_wave(Vector(2 * 32, 33 * 32), character.MeleeEnemy, 4, 48)),
                    action.add_updatables(self.create_wave(Vector(12 * 32, 36 * 32), character.MeleeEnemy, 5, 64))
                ]
            )
        )

        # boss, dialog, win when all enemies are dead
        self.add_trigger(
            trigger.trigger(self, 'should_spawn_boss'),
            action.action_list(
                [
                    action.add_updatable(character.WarlordBoss(Vector(random.uniform(32*5,32*15), 32 * 48 - 8),
                                                               self.player_character)),
                    action.add_trigger(
                        self,
                        trigger.trigger(self, 'all_enemies_dead'),
                        action.action_list(
                            [
                                action.action(self, 'play_dialog', 'data/dialog/act_one_warlord_1.json'),
                                action.action(self, 'end_with',
                                              game.SceneState.succeeded,
                                              updatable.fade_to_black(0.5))
                            ]
                        )
                    )
                ]
            )
        )


    def should_spawn_boss(self):
        return self.all_enemies_dead() and self.player_character.position.y > (43 * 32)


    def should_spawn_wave_2(self):
        return self.all_enemies_dead() and self.player_character.position.y > (15 * 32)


    def should_spawn_wave_3(self):
        return self.all_enemies_dead() and self.player_character.position.y > (27 * 32)

class ActTwo(Scene):

    def __init__(self):
        super(ActTwo, self).__init__('data/levels/act_two.json')

        # create player
        self.player_character = character.GirlCharacter(Vector(32 * 11, 32 * 5))
        self.player_character.ability_one = None
        self.add_updatable(self.player_character)

        # set camera
        self.set_camera(camera.PlayerCamera(self.player_character, 32 * 20))

        # create some enemies
        self.add_updatables(self.create_wave(Vector(32 * 10, 32 * 8), character.MeleeEnemy, 1, 0))

        # start by fading from black
        self.add_updatable(updatable.fade_from_black(1.0))

        # set up some triggers

        # lose when the player dies
        self.add_trigger(
            trigger.trigger(self, 'is_player_dead'),
            action.action_list(
                [
                    action.action(self, 'play_dialog', 'data/dialog/death_dialog.json'),
                    action.action(self, 'end_with',
                                  game.SceneState.failed,
                                  updatable.fade_to_black(0.5))
                ]
            )
        )

        """
        self.add_trigger(
            trigger.trigger(self, 'all_enemies_dead'),
            action.action_list(
                [
                    self.add_trigger(
                        trigger.trigger(self, 'player_in_area'),
                        action.action_list(
                            # Start Recluse cutscene
                        )
                    )
                ]
            )
        )
        """


class Cutscene(object):
    pass
