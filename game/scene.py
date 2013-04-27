import character
import inputs
import level
import renderer
from kidgine.math.vector import Vector


class Scene(object):
    def __init__(self, level_name):
        self.level,self.level_renderable = level.load(level_name)
        self.drawable = renderer.SceneRenderer(self.level_renderable)


    def update(self, t, dt):
        pass


class CombatScene(Scene):
    def __init__(self, level_name):
        super(CombatScene, self).__init__(level_name)

        self._inputs = inputs.Inputs()

        self.character = character.GirlCharacter()
        self.drawable.add_character(self.character)


    def update(self, t, dt):
        self._inputs.update(self.drawable.keystate)

        direction = Vector(self._inputs.leftright * 100, self._inputs.updown * 100)
        self.character.update(t, dt, direction)


class Cutscene(object):
    pass
