from pyglet.window import key


class Inputs(object):
    # WASD by default
    up_key     = key.W
    left_key   = key.A
    down_key   = key.S
    right_key  = key.D

    def __init__(self):
        self._reset()


    def _reset(self):
        self.up = False
        self.down = False
        self.left = False
        self.right = False

        self.updown = 0
        self.leftright = 0


    def update(self, keys):
        self._reset()

        # init movement actions
        if keys[self.up_key] and not keys[self.down_key]:
            self.up = True
        elif keys[self.down_key] and not keys[self.up_key]:
            self.down = True

        if keys[self.left_key] and not keys[self.right_key]:
            self.left = True
        elif keys[self.right_key] and not keys[self.left_key]:
            self.right = True

        if self.up:
            self.updown = 1
        elif self.down:
            self.updown = -1

        if self.left:
            self.leftright = -1
        elif self.right:
            self.leftright = 1
