from kidgine.math.vector import Vector
import kidgine.renderer.camera


class VerticalPanningCamera(kidgine.renderer.camera.CenteredCamera):
    def __init__(self, anchor, center_x, width):
        self._anchor = anchor
        self._x = center_x
        self._last = 0
        def anchor_fn():
            if self._anchor is not None:
                self._last = self._anchor.position.y
            return Vector(self._x, self._last)

        super(VerticalPanningCamera, self).__init__(anchor_fn, Vector(width))


class PlayerCamera(kidgine.renderer.camera.CenteredCamera):
    def __init__(self, anchor, width):
        self.anchor = anchor
        def anchor_fn():
            if self.anchor is not None:
                return self.anchor.position
            return Vector()

        super(PlayerCamera, self).__init__(anchor_fn, Vector(width))
