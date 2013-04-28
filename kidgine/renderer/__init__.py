import logging

import pyglet
from pyglet.gl import *

import monkey_patch
from ..config import RangeVar, BooleanVar


logger = logging.getLogger(__name__)

class Renderer(object):
    def __init__(self, configs, caption='', icon=None):
        width      = configs.client.get('cl_screen_width')
        height     = configs.client.get('cl_screen_height')
        fullscreen = configs.client.get('cl_fullscreen')
        vsync      = configs.client.get('cl_vsync')

        monkey_patch.patch_idle_loop()

        gl_config = pyglet.gl.Config(
            double_buffer = True,
            stencil_size  = 8,
            depth_size    = 0,
            red_size      = 8,
            green_size    = 8,
            blue_size     = 8,
            alpha_size    = 8)

        self._window = pyglet.window.Window(
            width=width, height=height, fullscreen=fullscreen, vsync=vsync, config=gl_config, caption=caption)

        if icon:
            self._window.set_icon(icon)

        self._window.push_handlers(self)

        self.drawables = list()

        configs.client.obj('cl_fullscreen').window = self._window
        configs.client.obj('cl_vsync').window = self._window
        configs.client.obj('cl_screen_width').window = self._window
        configs.client.obj('cl_screen_height').window = self._window

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)


    def add_drawable(self, order, drawable):
        self.drawables.append((order, drawable))
        self.drawables = sorted(self.drawables)

        # always deliver on_resize events: want to make sure handlers
        # that implement them always know the window size
        try:
            fn = getattr(drawable, 'on_resize')
        except AttributeError:
            pass
        else:
            fn(self._window.width, self._window.height)


    def remove_drawable(self, drawable):
        for index, (order, d) in enumerate(self.drawables):
            if d == drawable:
                del self.drawables[index]


    def on_draw(self, t, dt):
        self._window.clear()

        for order,drawable in self.drawables:
            drawable.draw(t, dt, self._window)

        self._window.flip()


    def _do_event(self, op, *args, **kwargs):
        for order,drawable in reversed(self.drawables):
            try:
                fn = getattr(drawable, op)
            except AttributeError:
                pass
            else:
                r = fn(*args, **kwargs)
                if r == pyglet.event.EVENT_HANDLED:
                    return r


    def on_resize(self, width, height):
        return self._do_event('on_resize', width, height)


    def on_text(self, text):
        return self._do_event('on_text', text)


    def on_text_motion(self, motion, select=False):
        return self._do_event('on_text_motion', motion, select)


    def on_text_motion_select(self, motion):
        return self._do_event('on_text_motion_select', motion)


    def on_key_press(self, symbol, modifiers):
        return self._do_event('on_key_press', symbol, modifiers)


    def on_key_release(self, symbol, modifiers):
        return self._do_event('on_key_release', symbol, modifiers)


    def on_mouse_motion(self, x, y, dx, dy):
        return self._do_event('on_mouse_motion', x, y, dx, dy)


    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return self._do_event('on_mouse_scroll', x, y, scroll_x, scroll_y)


    def on_mouse_press(self, x, y, button, modifiers):
        return self._do_event('on_mouse_press', x, y, button, modifiers)


    def on_mouse_release(self, x, y, button, modifiers):
        return self._do_event('on_mouse_release', x, y, button, modifiers)


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return self._do_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)


class _WindowVar(object):
    def __init__(self, attr, *args, **kwargs):
        self._window = None
        self._attr = attr
        super(_WindowVar, self).__init__(*args, **kwargs)

    def get(self):
        if self._window is not None:
            return getattr(self._window, self._attr)
        else:
            return super(_WindowVar, self).get()


    def _set_internal(self, value):
        super(_WindowVar, self)._set_internal(value)
        if self._window is not None and self.get() != value:
            try:
                setattr(self._window, self._attr, value)
            except AttributeError:
                pass # this is mostly to support FullscreenVar, which reimplements this


    def _set_window(self, window):
        self._window = window
        self._set_internal(self.value)


    def _get_window(self):
        return self._window

    window = property(_get_window, _set_window)


class HeightVar(_WindowVar, RangeVar):
    def __init__(self, default_value):
        super(HeightVar, self).__init__('height', default_value, 480, 3000)


class WidthVar(_WindowVar, RangeVar):
    def __init__(self, default_value):
        super(WidthVar, self).__init__('width', default_value, 640, 4000)


class VsyncVar(_WindowVar, BooleanVar):
    def __init__(self, default_value):
        super(VsyncVar, self).__init__('vsync', default_value)

    def _set_internal(self, value):
        super(VsyncVar, self)._set_internal(value)
        if self._window is not None and self.get() != value:
            self._window.set_vsync(value)


class FullscreenVar(_WindowVar, BooleanVar):
    def __init__(self, default_value):
        super(FullscreenVar, self).__init__('fullscreen', default_value)

    def _set_internal(self, value):
        super(FullscreenVar, self)._set_internal(value)
        if self._window is not None and self.get() != value:
            self._window.set_fullscreen(value)
