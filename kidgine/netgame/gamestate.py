import collections
import logging
import random

import level
from ..collision import CollisionDetector
from ..net import serializedobject


logger = logging.getLogger(__name__)

class LifeMsgHolder(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'time' : serializedobject.float,
        'obj'  : serializedobject.Polymorphic }

    def __init__(self, time = 0.0, obj = None):
        self.time = time
        self.obj = obj



class LifeMessages(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'births' : serializedobject.Dict(
            serializedobject.uint, LifeMsgHolder, 1),
        'deaths' : serializedobject.Dict(
            serializedobject.uint, LifeMsgHolder, 1), }

    def __init__(self):
        self.births = dict()
        self.deaths = dict()



class StaticGamestate(object):
    def __init__(self, state, level_obj, collision_detector):
        self.entities = dict()
        self.state = state
        if level_obj is not None:
            self._load_level(level_obj, collision_detector)


    def _load_level(self, level_obj, collision_detector):
        self.entities.clear()

        id = 0
        for entity in level_obj.static_entities:
            if entity.collidable is not None:
                collision_detector.update_collidable(id, entity.collidable)
            self.entities[id] = entity
            id += 1



class DynamicGamestate(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'entities' : serializedobject.Dict(
            serializedobject.uint, serializedobject.Polymorphic, 2) }

    def __init__(self):
        self.entities = dict()



class Gamestate(object):
    def __init__(self, configs):
        self.configs = configs

        self.collisiondetector = CollisionDetector()

        self._static = None
        self._dynamic = None
        self.load_level(None)


    # the following functions are run on both the client and the server

    def clear(self):
        if self._static:
            self._static.entities.clear()
        if self._dynamic:
            self._dynamic.entities.clear()

        self.collisiondetector.clear()


    def load_level(self, level_obj):
        self.clear()
        self._static = StaticGamestate(self, level_obj, self.collisiondetector)
        self._dynamic = DynamicGamestate()


    def set_entity(self, id, entity):
        entity.added(id, self)
        self._dynamic.entities[id] = entity


    def remove_entity(self, id):
        self._dynamic.entities[id].removed(self)
        del self._dynamic.entities[id]


    def entities(self):
        for e in self._static.entities.itervalues():
            yield e

        for e in self._dynamic.entities.itervalues():
            yield e


    # used for prediction on the client
    def simulate_player_input(self, t, id, inputs):
        self._dynamic.entities[id].simulate_input(t, inputs, self.collisiondetector)


    def update_shared(self, t, dt):
        self.collisiondetector.start_frame()
        for e in self._dynamic.entities.itervalues():
            e.update_shared(self.collisiondetector, t, dt)


class _PlayerData:
    def __init__(self, player):
        self.player = player



class _LifecycleEvents(object):
    TYPE_BIRTH = 1
    TYPE_DEATH = 2
    def __init__(self):
        self.events = collections.OrderedDict()


    def add(self, id, type, obj, t):
        self.events[id] = (obj, type, t)


    def update(self):
        while len(self.events) > 4096:
            self.events.popitem(last=False)


class GamestateServerController(object):
    def __init__(self, configs):
        self._level_name = None
        self.state = Gamestate(configs)
        self.id_counter = 10000
        self._player_data = dict()
        self._events = _LifecycleEvents()


    def loaded_level_name(self):
        return self._level_name


    def load_level(self, path):
        if len(path) > 0:
            level_obj = level.load(path)
            if level_obj is None:
                return False
            self.state.load_level(level_obj)

            for entity in level_obj.dynamic_entities:
                self.add_entity(entity, 0)

            self.do_load(level_obj)

            logger.info('Loaded level at {}'.format(path))
            self._level_name = path
            return True


    def do_load(self, level_obj):
        pass


    def create_player(self, t):
        player_data = _PlayerData(None)
        self.init_player_data(player_data)

        p = self._create_player_internal(t, player_data)

        id = self.generate_player_id()
        self._events.add(id, _LifecycleEvents.TYPE_BIRTH, p.copy(), t)
        self.state.set_entity(id, p)

        player_data.player = p
        self._player_data[id] = player_data

        return id


    def init_player_data(self, data):
        pass


    def _set_player(self, id, p, t):
        self.state.set_entity(id, p)
        self._player_data[id].player = p


    def remove_player(self, id, t):
        if id in self._player_data:
            del self._player_data[id]
        self.remove_entity(id, t)


    def add_entity(self, e, t):
        id = self.generate_entity_id()
        self._events.add(id, _LifecycleEvents.TYPE_BIRTH, e.copy(), t)
        self.state.set_entity(id, e)
        return id


    def remove_entity(self, id, t):
        if id in self.state._dynamic.entities:
            self._events.add(id, _LifecycleEvents.TYPE_DEATH, self.state._dynamic.entities[id].copy(), t)
            self.state.remove_entity(id)


    def entity_is_alive(self, id):
        return id in self.state._dynamic.entities and self.state._dynamic.entities[id].alive


    def simulate_player_input(self, t, id, inputs):
        self.state.simulate_player_input(t, id, inputs)


    def update_shared(self, t, dt):
        self.state.update_shared(t, dt)


    def update(self, t, dt):
        new_entities = list()
        for e in self.state._dynamic.entities.itervalues():
            l = e.update(self.state.collisiondetector, t, dt)
            if l is not None:
                new_entities.extend(l)

        # add new entities
        for e in new_entities:
            self.add_entity(e, t)

        # remove dead entities
        for id in self.state._dynamic.entities.keys():
            if not self.state._dynamic.entities[id].alive:
                self.remove_entity(id, t)

        # clean up old lifecycle events
        self._events.update()


    def generate_player_id(self):
        return self._unique_id(self.state._dynamic.entities)


    def generate_entity_id(self):
        id = self.id_counter
        self.id_counter += 1
        return id


    def _unique_id(self, dict_to_search):
        duplicate = True
        r = 0
        while duplicate and r < 10000: # ids below 10000 reserved for static levels
            r = random.getrandbits(32)
            # ensure this is unique
            duplicate = r in dict_to_search

        return r


    def _create_player_internal(self, player_data):
        return None
