import character
import inputs
import kidgine.collision
import level
import renderer
from kidgine.math.vector import Vector


class Scene(object):
    def __init__(self, level_name, collision_detector=None):
        self.level,self.level_renderable = level.load(level_name, collision_detector)
        self.drawable = renderer.SceneRenderer(self.level_renderable)


    def update(self, t, dt):
        pass


class CombatScene(Scene):
    def __init__(self, level_name):
        self._inputs = inputs.Inputs()
        self._collision_detector = kidgine.collision.CollisionDetector()

        super(CombatScene, self).__init__(level_name, self._collision_detector)

        self.character = character.GirlCharacter(self._collision_detector)
        self.character.position = Vector(32 * 10, 32 * 10)

        self.enemy = character.MeleeEnemy(self.character, self._collision_detector)
        self.enemy.position = Vector(32 * 8, 32 * 8)

        self.drawable.add_character(self.character)
        self.drawable.add_character(self.enemy)


    def update(self, t, dt):
        self._collision_detector.start_frame()
        self._inputs.update(self.drawable.keystate)

        self.character.update(t, dt, self._inputs, self._collision_detector)
        self.enemy.update(t, dt, self._collision_detector)


class Cutscene(object):
    pass
