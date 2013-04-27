import logging

import utils
from ..math import vector, remap


logger = logging.getLogger(__name__)

class CenteredCamera(object):
    def __init__(self, anchor, size):
        self.anchor = anchor
        self.world_size = size
        self.window_size = vector.one()


    def on_resize(self, width, height):
        self.window_size = vector.Vector(width, height)


    def apply(self):
        pos = self._get_size()
        utils.ortho_projection(pos.x, pos.y, self.world_size.x, self.world_size.y)


    def _get_size(self):
        pos = self._get_anchor()
        pos -= 0.5 * self.world_size
        return pos


    def _get_anchor(self):
        pos = vector.zero()
        if self.anchor is not None:
            pos = self.anchor()

        return pos


    def world_to_screen(self, position):
        """Take a position in world space and transform it to screen
        space."""
        anchor = self._get_anchor()

        x = remap(position.x,
                        (anchor.x - self.world_size.x / 2.0), (anchor.x + self.world_size.x / 2.0),
                        0., self.window_size.x)

        y = remap(position.y,
                        (anchor.y - self.world_size.y / 2.0), (anchor.y + self.world_size.y / 2.0),
                        0., self.window_size.y)

        return vector.Vector(x, y)


    def screen_to_world(self, position):
        anchor = self._get_anchor()

        x = remap(position.x,
                        0., self.window_size.x,
                        (anchor.x - self.world_size.x / 2.0), (anchor.x + self.world_size.x / 2.0))

        y = remap(position.y,
                        0., self.window_size.y,
                        (anchor.y - self.world_size.y / 2.0), (anchor.y + self.world_size.y / 2.0))

        return vector.Vector(x, y)


    def anchor_position_to_screen_coords(self):
        return self.world_to_screen(self._get_anchor())
