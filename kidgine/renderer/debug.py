import Queue
import logging

import pyglet

import utils


logger = logging.getLogger(__name__)


parent_group = pyglet.graphics.Group()
background = pyglet.graphics.OrderedGroup(0, parent_group)
foreground = pyglet.graphics.OrderedGroup(10, parent_group)

class DebugOverlay(object):
    def __init__(self, cmd_handler, configs):
        self._clock = pyglet.clock.ClockDisplay()
        self.configs = configs

        self.console_batch = pyglet.graphics.Batch()
        self.net_stats_batch = pyglet.graphics.Batch()

        width = configs.client.get('cl_screen_width')
        height = 200
        self.debug_console = ConsoleWidget(
            '> ', 0, 0, width, height, self.console_batch)
        self.debug_console.on_cmd_callback = cmd_handler

        logger = logging.getLogger() # log everything to this guy!
        self.handler = _ConsoleHandler(self.debug_console)
        logger.addHandler(self.handler)

        self.net_stats = None

        self.console_visible = False
        self.net_stats_visible = False


    def set_connection(self, connection):
        if self.net_stats is not None:
            self.net_stats.delete()

        if connection is not None:
            screen_width = self.configs.client.get('cl_screen_width')
            width = 450
            self.net_stats = NetStatsWidget(
                connection, screen_width - width, 0, width, 84, self.net_stats_batch)
        else:
            self.net_stats = None


    def update(self, dt):
        if self.net_stats is not None:
            self.net_stats.update()


    def draw(self, window):
        # grab all logged messages since last update and process
        self.handler.process_all()

        utils.screen_projection(window)
        self._clock.draw()
        if self.net_stats_visible and self.net_stats is not None:
            self.net_stats_batch.draw()
        if self.console_visible:
            self.console_batch.draw()


    def on_resize(self, width, height):
        self.debug_console.resize(0, 0, width, 200)


    def on_text(self, text):
        if self.console_visible:
            if len(text) == 1 and text[0] == '`':
                return pyglet.event.EVENT_HANDLED
            else:
                self.debug_console.on_text(text)
                return pyglet.event.EVENT_HANDLED


    def on_text_motion(self, motion, select=False):
        if self.console_visible:
            self.debug_console.on_text_motion(motion, select)
            return pyglet.event.EVENT_HANDLED


    def on_text_motion_select(self, motion):
        if self.console_visible:
            self.debug_console.on_text_motion_select(motion)
            return pyglet.event.EVENT_HANDLED


    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.GRAVE:
            self.console_visible = not self.console_visible
            return pyglet.event.EVENT_HANDLED
        elif self.console_visible:
            if symbol == pyglet.window.key.ESCAPE:
                self.console_visible = False
            return pyglet.event.EVENT_HANDLED
        elif symbol == pyglet.window.key.N:
            self.net_stats_visible = not self.net_stats_visible
            return pyglet.event.EVENT_HANDLED


    def on_key_release(self, symbol, modifiers):
        if self.console_visible:
            return pyglet.event.EVENT_HANDLED


    def on_mouse_motion(self, x, y, dx, dy):
        if self.console_visible:
            return pyglet.event.EVENT_HANDLED


    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.console_visible:
            self.debug_console.on_mouse_scroll(x, y, scroll_x, scroll_y)
            return pyglet.event.EVENT_HANDLED


    def on_mouse_press(self, x, y, button, modifiers):
        if self.console_visible:
            self.debug_console.on_mouse_press(x, y, button, modifiers)
            return pyglet.event.EVENT_HANDLED


    def on_mouse_release(self, x, y, button, modifiers):
        if self.console_visible:
            return pyglet.event.EVENT_HANDLED


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.console_visible:
            self.debug_console.on_mouse_drag(x, y, dx, dy, buttons, modifiers)
            return pyglet.event.EVENT_HANDLED


class NetStatsWidget(object):
    def __init__(self, connection, x, y, width, height, batch):
        self._connection = connection
        self._batch = batch

        self.rectangle = None
        self.text = None

        self.resize(x, y, width, height)

        self.text = pyglet.text.Label(
            self._connection.format_connection_stats(),
            font_name=['monaco', 'monospaced'],
            font_size=8.0,
            multiline=True,
            width=600,
            x=self.x,
            y=self.y,
            anchor_y = 'bottom',
            group=foreground,
            batch=self._batch)
        self.text.color=(0,0,0,255)


    def delete(self):
        if self.rectangle is not None:
            self.rectangle.delete()

        if self.text is not None:
            self.text.delete()


    def resize(self, x, y, width, height):
        self.width = width
        self.height = height

        self.x = x
        self.y = y

        self.update()

        if self.rectangle is not None:
            self.rectangle.delete()

        self.rectangle = _Rectangle(
            self.x, self.y, self.x + self.width, self.y + self.height, self._batch)


    def update(self):
        if self.text is not None:
            self.text.begin_update()
            self.text.text = self._connection.format_connection_stats()
            self.text.end_update()


class ConsoleWidget(object):
    def __init__(self, prompt, x, y, width, height, batch):
        self._batch = batch

        style = {'font_size':10}
        self.entry_widget = _ConsoleEntryWidget(prompt, self.on_cmd, batch, style)
        self.history_widget = _ConsoleHistoryWidget(batch, style)


        self.resize(x, y, width, height)


    def on_cmd(self, cmd):
        self.history_widget.add_line(cmd, {'bold':True,'color':(0,0,0,255)})
        if self.on_cmd_callback is not None:
            self.on_cmd_callback.on_cmd(cmd)


    def resize(self, x, y, width, height):
        self.entry_widget.set_size(x, y, width)
        self.history_widget.set_size(
            x, y + self.entry_widget.height, width, height - self.entry_widget.height)

        pad = 2
        self.rectangle = _Rectangle(x - pad, y - pad,
                                    x + width + pad, y + height + pad, self._batch)


    # the following are input events
    # we will eat all events! debug console is modal
    def on_text(self, text):
        self.entry_widget.caret.on_text(text)


    def on_text_motion(self, motion, select=False):
        return self.entry_widget.caret.on_text_motion(motion, select)


    def on_text_motion_select(self, motion):
        return self.entry_widget.caret.on_text_motion_select(motion)


    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        return self.entry_widget.caret.on_mouse_scroll(x, y, scroll_x, scroll_y)


    def on_mouse_press(self, x, y, button, modifiers):
        return self.entry_widget.caret.on_mouse_press(x, y, button, modifiers)


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        return self.entry_widget.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)


class _ConsoleHistoryWidget(object):
    def __init__(self, batch, style=None):
        self._batch = batch

        self.document = pyglet.text.document.FormattedDocument('debug console init')
        self.document.set_style(0, len(self.document.text), style)


    def set_size(self, x, y, width, height):
        try:
            self.layout.delete()
        except AttributeError:
            pass
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width, height, multiline=True, batch=self._batch)
        self.layout.x = x
        self.layout.y = y


    def add_line(self, text, attributes=None):
        text = '\n' + text
        self.document.insert_text(len(self.document.text), text, attributes)
        self.layout.view_y = -self.layout.content_height


class _ConsoleEntryWidget(object):
    def __init__(self, prompt, on_cmd_callback, batch, style=None):
        self._batch = batch

        self.prompt = prompt
        self.on_cmd_callback = on_cmd_callback
        self.document = pyglet.text.document.UnformattedDocument(self.prompt)
        self.document.set_style(0, len(self.document.text), style)
        font = self.document.get_font()

        self.height = font.ascent - font.descent


    def set_size(self, x, y, width):
        try:
            self.layout.delete()
            self.caret.delete()
        except AttributeError:
            pass
        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width, self.height, batch=self._batch)

        self.layout.x = x
        self.layout.y = y

        self.caret = _ConsoleCaret(len(self.document.text), self._on_enter, self.layout)


    def _on_enter(self):
        cmd = self.document.text[len(self.prompt):]
        self.document.text = self.prompt
        self.caret.reset()
        if self.on_cmd_callback is not None:
            self.on_cmd_callback(cmd)


class _ConsoleHandler(logging.Handler):
    def __init__(self, console):
        logging.Handler.__init__(self)
        self.console = console
        self.level = logging.INFO

        self.base_style = dict()
        self.base_style['bold'] = False
        self.base_style['italic'] = False
        self.base_style['underline'] = None
        self.base_style['color'] = (0, 0, 0, 255)

        debug_style = self.base_style.copy()
        debug_style['color'] = (0, 255, 0, 255)

        info_style = self.base_style.copy()

        warning_style = self.base_style.copy()
        warning_style['color'] = (255, 0, 0, 255)

        error_style = warning_style.copy()
        error_style['bold'] = True

        critical_style = error_style.copy()
        critical_style['underline'] = (255, 0, 0, 255)

        self.styles = dict()
        self.styles[logging.DEBUG]    = debug_style
        self.styles[logging.INFO]     = info_style
        self.styles[logging.WARNING]  = warning_style
        self.styles[logging.ERROR]    = error_style
        self.styles[logging.CRITICAL] = critical_style

        self.queue = Queue.Queue()


    def process_all(self):
        while True:
            try:
                record = self.queue.get_nowait()
                self._emit(record)
            except Queue.Empty:
                return


    def emit(self, record):
        """Why do we simply put the record on the queue? This logger ends up
        drawing GL commands; calling add_line in _emit actually
        creates some GL primitives. GL is single threaded; we must
        synchronize all GL calls. Because logging can happen on any
        thread, we use this mechanism to ensure we only ever access GL
        from a single thread. process_all should be called
        periodically (on the GL thread!) to process logs"""

        self.queue.put(record)


    def _emit(self, record):
        if record.levelno in self.styles:
            style = self.styles[record.levelno]
        else:
            logger.warning('No style for {} defined'.format(record.levelname))
            style = self.base_style

        self.console.history_widget.add_line(self.format(record), style)


class _ConsoleCaret(pyglet.text.caret.Caret):
    def __init__(self, prompt_len, on_enter_callback, layout, batch=None, color=(0, 0, 0)):
        super(_ConsoleCaret, self).__init__(layout, batch, color)
        self.prompt_len = prompt_len
        self.on_enter_callback = on_enter_callback
        self.reset()


    def move_to_point(self, x, y):
        super(_ConsoleCaret, self).move_to_point(x, y)
        self._validate_state()


    def on_text_motion(self, motion, select=False):
        if motion != pyglet.window.key.MOTION_BACKSPACE or self.position > self.prompt_len:
            super(_ConsoleCaret, self).on_text_motion(motion, select)
        self._validate_state()


    def on_text(self, text):
        if len(text) == 1 and ord(text[0]) == 13: # 13 is carriage return
            self.on_enter_callback()
        else:
            super(_ConsoleCaret, self).on_text(text)


    def select_to_point(self, x, y):
        super(_ConsoleCaret, self).select_to_point(x, y)
        self._validate_state()


    def reset(self):
        self.position = self.prompt_len
        self.mark = None


    def _validate_state(self):
        self.position = max(self.position, self.prompt_len)
        if self.mark is not None:
            self.mark = max(self.mark, self.prompt_len)


class _Rectangle(object):
    '''Draws a rectangle into a batch.'''
    def __init__(self, x1, y1, x2, y2, batch):
        self.vertex_list = batch.add(
            4, pyglet.gl.GL_QUADS, background,
            ('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
            ('c4B', [210, 220, 240, 255] * 4))


    def delete(self):
        self.vertex_list.delete()
