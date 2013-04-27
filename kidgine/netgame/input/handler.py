class InputHandler(object):
    def __init__(self, keystate):
        self._keystate = keystate

        self._screen_width = 1
        self._screen_height = 1

        # init variables that are not reset each frame
        self._mouse_x = 0
        self._mouse_y = 0
        self._mouse_sx = 0
        self._mouse_sy = 0

        self._mouse_held = 0

        self._mouse_pressed = 0
        self._mouse_released = 0

    #
    # Subclass API - override the following in subclasses
    #

    def do_begin_frame(self, input_state):
        pass


    def do_end_frame(self, input_state):
        pass


    def do_update(self, input_state):
        pass

    #
    # Internal functions
    #


    def begin_frame(self, input_state):
        self.do_begin_frame(input_state)
        self.do_update(self._keystate, input_state)
        try:
            fn = input_state.begin_pack
        except AttributeError:
            pass
        else:
            fn()


    def end_frame(self, input_state):
        self._mouse_pressed = 0
        self._mouse_released = 0

        self.do_end_frame(input_state)


    def on_resize(self, width, height):
        self._screen_width = width
        self._screen_height = height


    def on_key_press(self, symbol, modifiers):
        pass


    def on_key_release(self, symbol, modifiers):
        pass


    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_x = x
        self._mouse_y = y


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self._mouse_x = x
        self._mouse_y = y


    def on_mouse_press(self, x, y, button, modifiers):
        self._mouse_x = x
        self._mouse_y = y

        self._mouse_sx = x
        self._mouse_sy = y

        self._mouse_pressed |= button
        self._mouse_held |= button


    def on_mouse_release(self, x, y, button, modifiers):
        self._mouse_x = x
        self._mouse_y = y

        self._mouse_released |= button
        self._mouse_held ^= button
