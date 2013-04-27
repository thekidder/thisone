import logging
import os

import pyglet.resource


logger = logging.getLogger(__name__)

class CommandParser(object):
    def __init__(self, command_runner, configs):
        self.command_runner = command_runner
        self.configs = configs


    def on_cmd(self, cmd):
        cmd = cmd.split()

        if len(cmd) == 0:
            return

        args = cmd[1:]
        cmd = cmd[0]

        if ((self.configs.client is not None and self.configs.client.has(cmd)) or
            self.configs.server.has(cmd)):
            args = [cmd] + args

            if len(args) == 1:
                cmd = 'get_'
            else:
                cmd = 'set_'

            if self.configs.server.has(args[0]):
                cmd += 'svar'
            else:
                cmd += 'cvar'

        if self.command_runner.has(cmd):
            self.command_runner.do(cmd, args)
        else:
            logger.warning('invalid command: {}'.format(cmd))



class CommandRunner(object):
    def __init__(self):
        self.local_cmds = dict()
        self.remote_cmds = dict()


    def add_local(self, cmd, callback):
        self.local_cmds[cmd] = callback


    def add_remote(self, cmd, callback):
        self.remote_cmds[cmd] = callback


    def has_local(self, cmd):
        return cmd in self.local_cmds


    def has_remote(self, cmd):
        return cmd in self.remote_cmds


    def has(self, cmd):
        return self.has_remote(cmd) or self.has_local(cmd)


    def do(self, cmd, args):
        if not self.has(cmd):
            raise ValueError('No such command in command runner: {}'.format(cmd))

        try:
            self.local_cmds[cmd](args)
        except KeyError:
            self.remote_cmds[cmd](args)



class ClientCommandRunner(object):
    def __init__(self, command_runner):
        self._command_runner = command_runner


    def has(self, cmd):
        return self._command_runner.has_local(cmd)


    def do(self, cmd, args):
        if not self.has(cmd):
            raise ValueErrror('No such command in command runner: {}'.format(cmd))

        self._command_runner.do(cmd, args)


def load_config_file(command_parser, app_name, name):
    path = pyglet.resource.get_settings_path(app_name)

    if not os.path.isdir(path):
        if os.path.exists(path):
            os.remove(path)
        os.makedirs(path)

    filename = path + "/" + name

    if os.path.exists(filename):
        file = open(filename, 'r')
        for line in file:
            command_parser.on_cmd(line)
