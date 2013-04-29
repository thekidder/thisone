from kidgine.math.vector import Vector
import kidgine.renderer.camera


class VerticalPanningCamera(kidgine.renderer.camera.CenteredCamera):
    def __init__(self, anchor, center_x, width, min_y):
        self._min_y = min_y
        self._anchor = anchor
        self._x = center_x
        self._last = 0
        def anchor_fn():
            if self._anchor is not None:
                self._last = self._anchor.position.y
                if self._last < self._min_y:
                    self._last = self._min_y
            return Vector(self._x, self._last)

        super(VerticalPanningCamera, self).__init__(anchor_fn, Vector(width))


class PlayerCamera(kidgine.renderer.camera.CenteredCamera):
    def __init__(self, player, width):
        self.player = player
        def anchor_fn():
            if self.player is not None:
                return self.player.position
            return Vector()

        super(PlayerCamera, self).__init__(anchor_fn, Vector(width))
