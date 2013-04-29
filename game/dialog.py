import json
import logging

import kidgine.utils
import renderable


PortraitFacing = kidgine.utils.enum('left', 'right')

logger = logging.getLogger(__name__)

class Dialog(object):
    default_portrait = None
    default_facing   = PortraitFacing.left
    default_name     = ''
    default_sound    = None
    default_dialog   = ''
    default_min_time = 0.0

    def __init__(self, filename):
        with open(filename) as f:
            data = json.load(f)

        self.lines = data['lines']
        self.current_line = -1
        self.request_dismiss = False
        self.renderable = None
        self._preprocess()
        self._transition(0)


    def _preprocess(self):
        for line in self.lines:
            if 'portrait' not in line:
                line['portrait'] = default_portrait

            if 'portrait_facing' in line:
                if line['portrait_facing'] == 'right':
                    line['portrait_facing'] = PortraitFacing.right
                else:
                    line['portrait_facing'] = PortraitFacing.left
            else:
                line['portrait_facing'] = default_facing

            if 'name' not in line:
                line['name'] = default_name

            if 'sound' not in line:
                line['sound'] = default_sound

            if 'dialog' not in line:
                line['dialog'] = default_dialog

            if 'minimum_time' not in line:
                line['minimum_time'] = default_min_time


    def get_current_line(self):
        return self.lines[self.current_line]


    def can_transition(self, t):
        return t - self.last_transition_time > self.lines[self.current_line]['minimum_time']


    def update(self, inputs, t, dt, c):
        if self.last_transition_time == 0:
            self.last_transition_time = t

        if self.can_transition(t):
            if inputs.dialog_dismiss:
                self._transition(t)


    def removed(self, c):
        pass


    def is_ui(self):
        return True


    def _transition(self, t):
        self.current_line += 1
        self.last_transition_time = t
        if self.current_line == len(self.lines):
            self.done = True
        else:
            if self.renderable:
                self.renderable.new_text()
            self.done = False
            # logger.info('{} {} {} {} {} {}'.format(
            #         self.lines[self.current_line]['portrait'],
            #         self.lines[self.current_line]['portrait_facing'],
            #         self.lines[self.current_line]['name'],
            #         self.lines[self.current_line]['sound'],
            #         self.lines[self.current_line]['dialog'],
            #         self.lines[self.current_line]['minimum_time']))


    def alive(self):
        return not self.done


    def create_renderable(self):
        def wrapped(batch, group):
            self.renderable = renderable.DialogRenderable(batch, group, self)
            return self.renderable
        return wrapped
