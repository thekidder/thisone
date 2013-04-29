import ability
import collision
import data.animations
import kidgine.utils
import renderable
from kidgine.math.vector import Vector


Tags = kidgine.utils.enum('enemy', 'boss', 'player', 'dialog', 'projectile', 'ability', 'level')

class TriggeredUpdatable(object):
    def __init__(self, trigger, action):
        self.trigger = trigger
        self.action = action
        self.triggered = False


    def update(self, inputs, t, dt, collision_detector):
        if self.trigger(inputs, t, dt, collision_detector):
            self.triggered = True
            return self.action(inputs, t, dt, collision_detector)


    def removed(self, collision_detector):
        pass


    def create_renderable(self):
        return None


    def get_tags(self):
        return set()


    def alive(self):
        return not self.triggered


class ActionEvent(TriggeredUpdatable):
    def __init__(self, action):
        def trigger(inputs, t, dt, collision_detector):
            return True
        super(ActionEvent, self).__init__(trigger, action)


class Bomb(object):
    explosion_time = data.animations.animation_duration('bomb_explosion')
    time = 1.5
    tags = set([Tags.projectile])
    counter = 0
    environment_filters = set([collision.Tags.ENVIRONMENT, kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])
    damage = 10
    slow_time = 0
    slow_factor = 1.0

    def __init__(self, position, throw_vector):
        self.position = position
        self.forces = throw_vector
        self.time_left = self.time
        self.explosion_time_left = self.explosion_time
        self.explosion_triggered = False


        tl = Vector(-32, -32)
        br = Vector( 32,  32)

        self.token = 'bomb{}'.format(Bomb.counter)
        Bomb.counter += 1
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        self.collidable.tags = set([
                collision.Tags.PROJECTILE,
                collision.Tags.PUSHABLE,
                collision.Tags.NOT_SLOWED])


    def collides(self, t, shape):
        if collision.Tags.PLAYER in shape.tags and not self.explosion_triggered:
            self._trigger()
            shape.owner.damage(t, self.damage)

        if collision.Tags.ENEMY in shape.tags and self.explosion_triggered:
            shape.owner.damage(t, self.damage)


    def slow(self, t, slow_factor, thing_that_is_slowing):
        if isinstance(thing_that_is_slowing, ability.Whirlpool):
            self.collidable.tags.discard(collision.Tags.NOT_SLOWED)
            self.slow_factor = slow_factor
            self.slow_time = t


    def is_ui(self):
        return False


    def alive(self):
        return self.explosion_time_left >= 0


    def apply_force(self, force):
        self.forces += force


    def removed(self, collision_detector):
        collision_detector.remove_collidable(self.token)


    def get_tags(self):
        return self.tags


    def _trigger(self):
        self.explosion_triggered = True


    def update(self, inputs, t, dt, collision_detector):
        if not self.explosion_triggered:
            self.time_left -= dt

            if self.time_left <= 0.0:
                self._trigger()

            self.position = self.position + self.forces * self.slow_factor

            all = collision_detector.collides(token=self.token,
                                              filters=self.environment_filters)
            if len(all) > 0:
                normal = Vector()
                for c in all:
                    if normal.dot(c.translation_vector) == 0:
                        normal += c.translation_vector
                self.position += normal

            collision_detector.update_collidable(self.token, self.collidable)

        else:
            self.explosion_time_left -= dt

        self.reset_slow(t)


    def reset_slow(self, t):
        # if we haven't been slowed in a while, reset
        if t - self.slow_time > 0.4:
            self.collidable.tags.add(collision.Tags.NOT_SLOWED)
            self.slow_factor = 1.0


    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.BombRenderable(batch, group, self)
        return wrapped



class Spear(Bomb):
    time = 1.0
    time_left = 0
    tags = set([Tags.projectile])
    counter = 0
    environment_filters = set([collision.Tags.ENVIRONMENT, kidgine.collision.shape.tags.IMPEEDS_MOVEMENT])
    damage = 10

    def __init__(self, position, throw_vector):
        self.position = position
        self.forces = throw_vector
        self.forced = False
        self.time_left = self.time

        tl = Vector(-20, -20)
        br = Vector( 20,  20)

        self.token = 'spear{}'.format(Spear.counter)
        Spear.counter += 1
        self.collidable = kidgine.collision.rectangle.Rectangle(self, tl, br)
        self.collidable.tags = set([
                collision.Tags.PUSHABLE])

    def collides(self, t, shape):
        if collision.Tags.PLAYER in shape.tags or \
                collision.Tags.ENEMY in shape.tags and self.forced:
            shape.owner.damage(t, self.damage)
            self.time_left = 0

    def alive(self):
        return self.time_left >= 0

    def apply_force(self, force):
        self.forces += force
        self.forced = True
        self.time_left = 1.0

    def update(self, inputs, t, dt, collision_detector):
        self.time_left -= dt

        self.position = self.position + self.forces

        all = collision_detector.collides(token=self.token,
                                          filters=self.environment_filters)
        if len(all) > 0:
            normal = Vector()
            for c in all:
                if normal.dot(c.translation_vector) == 0:
                    normal += c.translation_vector
            self.position += normal

        collision_detector.update_collidable(self.token, self.collidable)

    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.SpearRenderable(batch, group, self)
        return wrapped



class OpacityFader(object):
    def __init__(self, color, start, end, duration):
        self.r,self.g,self.b = color
        self.start = start
        self.end = end
        self.duration = duration
        self.time_left = duration
        self.opacity = start


    def removed(self, c):
        pass


    def update(self, inputs, t, dt, collision_detector):
        self.time_left -= dt
        self.opacity = kidgine.utils.lerp(
            (self.duration - self.time_left) / self.duration,
            self.start,
            self.end)


    def alive(self):
        return self.time_left >= 0


    def is_ui(self):
        return True


    def get_tags(self):
        return set()


    def create_renderable(self):
        def wrapped(batch, group):
            return renderable.OpacityFaderRenderable(batch, group, self)
        return wrapped


def fade_to_black(duration):
    return OpacityFader((0,0,0),0,1,duration)


def fade_from_black(duration):
    return OpacityFader((0,0,0),1,0,duration)
