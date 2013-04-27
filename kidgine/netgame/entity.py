from .. import utils
from ..math import vector
from ..net import serializedobject


class EntityReference(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        '_id' : serializedobject.uint }

    def __init__(self):
        self._id = 0
        self._lookup_dict = None


    def copy(self):
        e = EntityReference()
        e._id = self._id
        return e


    def added(self, id, gamestate):
        self._lookup_dict = gamestate._dynamic.entities


    def _get_obj(self):
        if self._lookup_dict is None or self._id == 0 or self._id not in self._lookup_dict:
            return None

        return self._lookup_dict[self._id]


    def _set_obj(self, obj):
        if obj is not None and obj.id != 0:
            self._id = obj.id
        else:
            self._id = 0


    def _get_id(self):
        return self._id


    id  = property(_get_id, None)
    obj = property(_get_obj, _set_obj)


# how an entity is displayed on the client
prediction_type = utils.enum(
    'PREDICTED',    # predict the the entity
    'INTERPOLATED', # interpolate the entity using the client's cl_interpolation value
    'NEWEST'        # always display the newest entity received from the server
)


class Entity(serializedobject.SerializedObject):
    _SERIALIZED_MEMBERS = {
        'position' : vector.Vector,
        'collidable' : serializedobject.Polymorphic }

    def __init__(self, position=vector.zero):
        super(Entity, self).__init__()

        self.alive = True
        self.position = position
        self.collidable = None
        self.collidable_token = None

        self.id = 0 # not serialized; only set when added/removed from gamestate


    # how is the entity displayed on the client? predicted, interpolated?
    def prediction_type(self, controlling_player):
        # by default, predicted if we're controlling this entity, otherwise interpolated
        if controlling_player == self.id:
            return prediction_type.PREDICTED
        else:
            return prediction_type.INTERPOLATED


    # called when we are added to the gamestate
    def added(self, id, gamestate):
        self.id = id
        self.configs = gamestate.configs
        if self.collidable is not None:
            self.collidable_token = id
            gamestate.collisiondetector.update_collidable(self.collidable_token, self.collidable)


    # called when we are removed from gamestate
    # note that this is *not* called when we are replaced in the
    # gamestate by a new entity - only when we are completely removed.
    def removed(self, gamestate):
        self.id = 0
        if self.collidable_token is not None:
            gamestate.collisiondetector.remove_collidable(self.collidable_token)


    # update_shared is called on the server and on the client for prediction
    def update_shared(self, collision_detector, t, dt):
        pass


    def update(self, collision_detector, t, dt):
        pass


    def update_position(self, collision_detector, new_position):
        old = self.position.copy()
        if new_position != self.position:
            self.position = new_position
            collision_detector.update_collidable(self.collidable_token, self.collidable)

        return self.position - old


    def before_pack(self):
        pass


    def after_unpack(self):
        self.collidable.owner = self


    def __str__(self):
        return '<{} at {}, collidable: {}>'.format(
            type(self), self.position, self.collidable)


    def interpolate(self, new, interp_time):
        e = type(self)(vector.interpolate(self.position, new.position, interp_time))
        return e


    def image_name(self):
        return 'notfound'
