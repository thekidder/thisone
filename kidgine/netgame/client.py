import Queue
import commands
import logging
import socket
import threading
import time
from collections import deque

import pyglet

import download_client
import entity
import gamestate
import level
import messages
from ..net import networkmanager
from ..renderer import debug


logger = logging.getLogger(__name__)


def _connected_function(fn):
    def wrapper(self, *args, **kwargs):
        if self._remote_address not in self._networkmanager.connected_peers():
            return
        else:
            addr = self._remote_address
            conn = self._networkmanager.get_connection(addr)

            return fn(self, addr, conn, *args, **kwargs)

    return wrapper


def _playing_function(fn):
    def wrapper(self, *args, **kwargs):
        if self._remote_address not in self._networkmanager.connected_peers():
            return

        playerid = None
        try:
            playerid = self._player_id
        except AttributeError:
            pass
        else:
            return fn(self, playerid, *args, **kwargs)

    return wrapper


class Client(object):
    FRAME_TIME    = 1/100.
    SEND_TIME     = 1/30.
    SEND_TIME_BAD = 1/10.

    def __init__(self, app_name, _renderer, input_state_type, configs, protocol, message_types):
        self._renderer = _renderer
        self.input_state = input_state_type()
        self._configs = configs

        # setup command parsers and runners
        self._command_runner = commands.CommandRunner()
        # add commands

        # add config commands
        self._configs.add_commands(self._command_runner)
        self._command_runner.add_remote('set_svar', self._set_svar)
        self._command_runner.add_remote('load', self._load_level)
        self._command_runner.add_local('net_stats', self.print_net_stats)

        self._command_parser = commands.CommandParser(self._command_runner, self._configs)

        # load config
        client_parser = commands.CommandParser(
            commands.ClientCommandRunner(self._command_runner), self._configs)
        commands.load_config_file(client_parser, app_name, 'config.txt')

        self._debug_overlay = None
        self._debug_overlay = debug.DebugOverlay(self._command_parser, self._configs)
        self._renderer.add_drawable(50, self._debug_overlay)

        self._all_update_fns = list()

        self._networkmanager = networkmanager.NetworkManager(
            protocol, message_types)

        self._networkmanager.register_connection_callbacks(self)

        # updatables
        pyglet.clock.schedule_interval(self._update_all, Client.FRAME_TIME)
        pyglet.clock.schedule_interval(self._log, 5.0)
        pyglet.clock.schedule_interval(self._debug_overlay.update, 0.25)

        self.schedule_for_update(self._update)

        # handler - for running things on the main thread
        self.handler = Queue.Queue()

        # register RPC functions
        self.register_receive_handler(
            messages.default_messages.types.GAMESTATE_UPDATE, self._on_gamestate_update)
        self.register_receive_handler(
            messages.default_messages.types.INIT_LEVEL, self._on_init_level)
        self.register_receive_handler(
            messages.default_messages.types.TIMESTAMP, self._on_timestamp)
        self.register_receive_handler(
            messages.default_messages.types.SVAR_UPDATE, self._on_svar_update)
        self.register_receive_handler(
            messages.default_messages.types.INVALID_CMD, self._on_invalid_cmd)

        self._remote_address = None

        self._input_commands = deque()

        # keep track of time
        self._localtime = 0
        self._accumulator = 0

        # keep a queue of gamestates around for interpolating
        # entities
        self._states = deque()
        self._last_server_time = 0
        # state visible to the player
        # interpolation between old state and new state, plus
        # client side prediction for the current player
        self._interpolated_state = gamestate.Gamestate(self._configs)

        self._gamerenderer = None

    #
    # Subclass interface
    #

    def register_receive_handler(self, type, method):
        self._networkmanager.register_receive_handler(type, method)


    def add_drawable(self, order, drawable):
        self._renderer.add_drawable(order, drawable)


    def remove_drawable(self, drawable):
        self._renderer.remove_drawable(drawable)


    @_playing_function
    def do_update(self, inputs, player_id, t, dt):
        """override this to perform logic on each update step"""
        pass


    def do_init_level(self, level_obj):
        """override this to perform logic when a level is loaded"""
        pass

    #
    # connection callbacks
    #

    def on_disconnect(self, addr):
        if self._debug_overlay:
            self._debug_overlay.set_connection(None)


    def on_connect(self, addr):
        conn = self._networkmanager.get_connection(addr)
        if self._debug_overlay:
            self._debug_overlay.set_connection(conn)


    #
    # RPC functions
    #

    @_playing_function
    def _on_gamestate_update(self, player_id, msg_id, data, addr):
        update_msg = messages.GamestateUpdateMsg
        data = update_msg.unpack(data)

        dynamic = update_msg.state
        life_msgs = update_msg.life_msgs
        last_input_command_ack = update_msg.last_input_ack

        new_state =  (dynamic, self._last_server_time, life_msgs)
        self._states.append(new_state)

        # purge old states
        time = self._get_interpolated_time()
        while len(self._states) > 2 and self._states[1][1] < time:
            # second-to-last state is older than interpolation time;
            # get rid of the oldest state
            self._states.popleft()

        old_player = None
        if player_id in self._interpolated_state._dynamic.entities:
            old_player = self._interpolated_state._dynamic.entities[player_id].copy()

        if player_id in new_state[0].entities:
            player_character = new_state[0].entities[player_id].copy()
            self._interpolated_state.set_entity(player_id, player_character)
            # replay input commands
            to_pop = 0
            for msg_id, input_command in self._input_commands:
                if msg_id <= last_input_command_ack:
                    to_pop += 1
                    continue

                self._interpolated_state.simulate_player_input(
                    self._localtime, player_id, input_command)

            while to_pop > 0:
                self._input_commands.popleft()
                to_pop -= 1


            if old_player is not None:
                new_player = self._interpolated_state._dynamic.entities[player_id]
                if not new_player.position.closer_than(old_player.position, 10):
                    logger.info('WARPING from {} to {}'.format(old_player.position, new_player.position))
                else:
                    # if we are pretty close to server position, just move a bit closer
                    self._interpolated_state.set_entity(player_id,
                                                        old_player.interpolate(new_player, .1))

        delta = self._localtime - new_state[1]


    def _on_init_level(self, msg_id, data, addr):
        msg = messages.InitLevelMsg
        msg.unpack(data)

        self._player_id = msg.player_id

        logger.info('init level {}. player id is {}'.format(msg.level_path, self._player_id))
        # clear old state
        self._states.clear()
        self._last_server_time = 0

        l = level.load(msg.level_path)

        if not l:
            client = download_client.DownloadClient(
                (self._remote_address[0], 4444),
                msg.level_path,
                self.handler,
                self._init_level)
            t = threading.Thread(target=client.download_level)
            t.daemon = True
            t.start()
        else:
            self._init_level(l)


    def _on_timestamp(self, msg_id, data, addr):
        msg = messages.TimestampMsg
        msg.unpack(data)
        latency = self._networkmanager.get_connection(addr).rtt / 2000.0
        self._localtime = msg.timestamp + latency
        self._last_server_time = msg.timestamp


    def _on_svar_update(self, msg_id, data, addr):
        msg = messages.SetSvarMsg
        msg.unpack(data)
        self._configs.server.set(msg.name, msg.value)
        logger.debug('got svar update; {} = {}'.format(
            msg.name, self._configs.server.get(msg.name)))


    def _on_invalid_cmd(self, msg_id, data, addr):
        msg = messages.InvalidCmdMsg
        msg.unpack(data)
        logger.warning(msg.message)


    #
    # Client commands
    #

    @_connected_function
    def print_net_stats(self, addr, conn, args=None):
        conn.print_connection_stats(logging.INFO)


    @_connected_function
    def _load_level(self, addr, conn, args):
        if len(args) != 1:
            logger.warning('invalid number of arguments to load')
            return

        name = args[0].encode('utf8')

        if len(name) > 255:
            logger.error('level name is too long')
            return

        msg = messages.LoadLevelMsg.set(name)
        data = msg.pack()
        self._networkmanager.send_immediate(
            self._remote_address, messages.default_messages.types.LOAD_LEVEL, data)


    @_connected_function
    def _set_svar(self, addr, conn, args):
        if len(args) != 2:
            logger.warning('invalid number of arguments to set_svar')
            return

        name = args[0].encode('utf8')
        value = args[1].encode('utf8')

        if len(name) > 255 or len(value) > 255:
            logger.error('svar name or value is too long')
            return

        msg = messages.SetSvarMsg.set(name, value)
        data = msg.pack()
        self._networkmanager.send_immediate(
            self._remote_address, messages.default_messages.types.SET_SVAR, data)

    #
    # Internal methods
    #

    def _update_all(self, dt):
        self._accumulator += dt

        while self._accumulator > Client.FRAME_TIME:
            self._do_tick(Client.FRAME_TIME)
            self._accumulator -= Client.FRAME_TIME

        self._renderer.on_draw()


    def _do_tick(self, dt):
        self.input_state.set_duration(dt)

        input_handler = None
        if self._gamerenderer is not None:
            input_handler = self._gamerenderer.input_handler
            input_handler.begin_frame(self.input_state)

        for i in self._all_update_fns:
            i(self.input_state, self._localtime, dt)

        if input_handler is not None:
            input_handler.end_frame(self.input_state)

        self._update_gametime(dt)


    @_connected_function
    def _update_gametime(self, addr, conn, dt):
        self._localtime += dt


    def _send_interval(self, conn):
        if conn.flowcontrol.good:
            return Client.SEND_TIME
        else:
            return Client.SEND_TIME_BAD


    def _log(self, dt):
        logger.debug("localtime is " + str(self._localtime))
        self._log_connected()

        logger.debug('----------------WORLD-------------------')
        logger.debug('\t# Static entities:  {}'.format(
            len(self._interpolated_state._static.entities)))
        logger.debug('\t# Dynamic entities: {}'.format(
            len(self._interpolated_state._dynamic.entities)))
        logger.debug('----------------------------------------')
        self._interpolated_state.collisiondetector.log_stats(logging.DEBUG)


    @_connected_function
    def _log_connected(self, addr, conn):
        logger.debug('-------------CONNECTION-----------------')
        conn.print_connection_stats(logging.DEBUG)


    def _init_level(self, level_obj):
        self._interpolated_state.load_level(level_obj)

        self.do_init_level(level_obj)


    def _update(self, inputs, t, dt):
        self._process_handler()

        self._update_connected(inputs, t, dt)

        if self._remote_address != None:
            self._networkmanager.connect(self._remote_address)

        self._networkmanager.update()



    @_connected_function
    def _update_connected(self, addr, conn, inputs, t, dt):
        # do interpolation and entity prediction
        self._interpolate_gamestate(dt, addr)

        # update entities
        self._interpolated_state.update_shared(t, dt)

        self.do_update(inputs, t, dt)

        # send all non-time critical messages
        if time.time() - conn.last_packet_send_time > self._send_interval(conn):
            self._networkmanager.send_all(addr)


    def _process_handler(self):
        while True:
            try:
                cmd = self.handler.get_nowait()
                cmd()
            except Queue.Empty:
                return


    @_playing_function
    def _interpolate_gamestate(self, playerid, dt, addr):
        # interpolate other entities
        # find the gamestates surrounding our interpolation time
        time_with_interpolation = self._get_interpolated_time()

        new_state = None
        old_state = None
        for state in reversed(self._states):
            if state[1] > time_with_interpolation:
                new_state = state
            elif state[1] < time_with_interpolation:
                old_state = state
                break

        base_state = new_state
        if base_state == None:
            base_state = old_state

        if base_state != None:
            s = self._interpolated_state._dynamic

            all_ids = set(s.entities.iterkeys())
            if old_state != None:
                all_ids |= set(old_state[0].entities.iterkeys())
            if new_state != None:
                all_ids |= set(new_state[0].entities.iterkeys())

            for id in all_ids:
                if id == playerid:
                    continue # going to do prediction

                if id in base_state[0].entities:
                    prediction_type =  base_state[0].entities[id].prediction_type(playerid)
                    if (prediction_type == entity.prediction_type.NEWEST or
                        prediction_type == entity.prediction_type.PREDICTED):
                        self._interpolated_state.set_entity(id, base_state[0].entities[id].copy())
                        continue

                if old_state != None and new_state != None:
                    # interpolation
                    old_time = old_state[1]
                    new_time = new_state[1]

                    if id in old_state[0].entities and id in new_state[0].entities:
                        interp_time = (time_with_interpolation - old_time) / (new_time - old_time)

                        e = old_state[0].entities[id].interpolate(
                            new_state[0].entities[id], interp_time)
                        self._interpolated_state.set_entity(id, e)
                    elif id in new_state[0].entities:
                        if id in new_state[2].births:
                            birth_time = new_state[2].births[id].time
                            if new_time > birth_time:
                                interp_time = ((time_with_interpolation - birth_time) /
                                               (new_time - birth_time))
                                if interp_time >= 0.0 and interp_time <= 1.0:
                                    e = new_state[2].births[id].obj.interpolate(
                                        new_state[0].entities[id], interp_time)
                                    self._interpolated_state.set_entity(id, e)
                        else:
                            self._interpolated_state.set_entity(id, new_state[0].entities[id].copy())
                    elif id in old_state[0].entities:
                        if id in new_state[2].deaths:
                            death_time = new_state[2].deaths[id].time
                            if death_time > old_time:
                                interp_time = ((time_with_interpolation - old_time) /
                                               (death_time - old_time))
                                if interp_time >= 0.0 and interp_time <= 1.0:
                                    e = old_state[0].entities[id].interpolate(
                                        new_state[2].deaths[id].obj, interp_time)
                                    self._interpolated_state.set_entity(id, e)
                                elif id in self._interpolated_state._dynamic.entities:
                                    self._interpolated_state.remove_entity(id)
                            elif id in self._interpolated_state._dynamic.entities:
                                self._interpolated_state.remove_entity(id)
                        else:
                             self._interpolated_state.set_entity(id, old_state[0].entities[id].copy())
                    else:
                        self._interpolated_state.remove_entity(id)

                else:
                    if id in base_state[0].entities:
                        # only have a single state; copy over entities
                        self._interpolated_state.set_entity(id, base_state[0].entities[id].copy())
                    else:
                        self._interpolated_state.remove_entity(id)


    def _get_interpolated_time(self):
        latency = self._networkmanager.get_connection(self._remote_address).rtt / 1000.0
        # use half of latency: only interested in latency from server -> client
        latency /= 2.0
        interpolation = self._configs.client.get('cl_interpolation')

        # TODO: something sophisticated to change interpolation based on latency
        # interpolation = max(interpolation, latency + 0.05)

        return self._localtime - interpolation


    def schedule_for_update(self, fn):
        self._all_update_fns.append(fn)


    def connect(self, addr):
        self._remote_address = socket.getaddrinfo(addr[0], addr[1], socket.AF_INET)[0][4]
        self._networkmanager.connect(self._remote_address)


    def run(self):
        pyglet.app.run()
