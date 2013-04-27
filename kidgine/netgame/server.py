import logging
import time

import download_server
import gamestate
import messages
from ..net import networkmanager


logger = logging.getLogger(__name__)

# use on RPC functions with signature (msg id, data, addr) and call wrapped function with
# signature (msg_id, data, addr, player_data)
def _valid_player_function(fn):
    def wrapper(self, msg_id, data, addr):
        try:
            player_data = self._all_players.get(addr)
        except InvalidPeer:
            pass
        else:
            fn(self, msg_id, data, addr, player_data)

    return wrapper

class _PlayerData(object):
    """class to store data about the last update sent to each client"""
    def __init__(self):
        self.id                     = -1
        self.last_input_acks        = 0
        self.last_update_time       = 0
        self.last_update_entity_set = set()


class _AllPlayers(object):
    """query players by id or address."""
    def __init__(self):
        self._all_players = dict()

    def all(self):
        return self._all_players.iteritems()

    def has(self, addr):
        return addr in self._all_players

    def get(self, addr):
        if addr not in self._all_players:
            self._all_players[addr] = _PlayerData()
        return self._all_players[addr]

    def get_from_id(self, id):
        for addr,data in self._all_players.iteritems():
            if data.id == id:
                return addr,data
        raise InvalidPeer()

    def remove(self, addr):
        del self._all_players[addr]


class Server(object):
    FRAME_TIME    = 1/100.
    SEND_TIME     = 1/30.
    SEND_TIME_BAD = 1/10.

    def __init__(self, app_name, configs, protocol, message_types, controller,
                 addr, port, download_server_port):
        self._controller = controller
        self.configs = configs

        addr = (addr, port)

        self._networkmanager = networkmanager.NetworkManager(protocol, message_types, addr)

        self.register_receive_handler(messages.default_messages.types.INPUT_COMMAND, self._on_input_update)
        self.register_receive_handler(messages.default_messages.types.SET_SVAR, self._on_set_svar)
        self.register_receive_handler(messages.default_messages.types.LOAD_LEVEL, self._on_load_level)

        self._networkmanager.register_connection_callbacks(self)

        self._log_time = 0
        self._update_rate_check_time = time.time()

        self._all_players = _AllPlayers()
        self._gametime = 0

        # keep track of perf
        self.frames = 0
        self.net_updates = 0

        # download server - let clients download assets from us
        self.download_server = download_server.DownloadServer((addr[0], download_server_port))

    #
    # Subclass interface
    #

    def register_receive_handler(self, type, method):
        self._networkmanager.register_receive_handler(type, method)


    def load_level(self, name, addr = None):
        success = self._controller.load_level(name)
        if not success and addr is not None:
            self._send_invalid_cmd_msg(addr, 'Map {} is invalid'.format(name))
        else:
            for addr,data in self._all_players.all():
                new_player_id = self._controller.create_player(self._gametime)
                data.id = new_player_id
                data = messages.InitLevelMsg.set(new_player_id, name).pack()
                self._networkmanager.send_immediate(
                    addr, messages.default_messages.types.INIT_LEVEL, data)


    def do_on_input_update(self, msg_id, payload, player):
        """override this to do logic on input_update messages"""
        pass


    #
    # RPC functions
    #

    @_valid_player_function
    def _on_input_update(self, msg_id, payload, addr, player_data):
        self.do_on_input_update(msg_id, payload, addr, player_data)


    @_valid_player_function
    def _on_set_svar(self, msg_id, payload, addr, player_data):
        msg = messages.SetSvarMsg
        msg.unpack(payload)

        # TODO: check for player permissions to set svars here
        self._set_svar(addr, player_data.id, msg.name, msg.value)


    @_valid_player_function
    def _on_load_level(self, msg_id, payload, addr, player_data):
        msg = messages.LoadLevelMsg
        msg.unpack(payload)

        self.load_level(msg.name, addr)

    #
    # Internal functions
    #

    def _set_svar(self, addr, player_id, name, value):
        if self.configs.server.is_valid(name, value):
            logger.info('player {} setting {} to {}'.format(
                    player_id, name, value))
            success = self.configs.server.set(name, value)
            if success:
                msg = self._get_svar_update_msg(name)
                data = msg.pack()

                self._networkmanager.broadcast(messages.default_messages.types.SVAR_UPDATE, data)
        else:
            logger.info('player {} tried to set {} to invalid value {}'.format(
                    player_id, name, value))

            self._send_invalid_cmd_msg(addr, self.configs.server.obj(name).valid_values())


    def _send_invalid_cmd_msg(self, addr, msg):
        msg = messages.InvalidCmdMsg.set(msg)
        data = msg.pack()

        self._networkmanager.queue(addr, messages.default_messages.types.INVALID_CMD, data)


    def _get_svar_update_msg(self, name):
        return messages.SetSvarMsg.set(name, str(self.configs.server.get(name)))


    def _send_interval(self, conn):
        if conn.flowcontrol.good:
            return Server.SEND_TIME
        else:
            return Server.SEND_TIME_BAD


    def _log(self):
        self._log_time = time.time()

        logger.info('-------------CONNECTIONS----------------')
        for addr in self._networkmanager.connected_peers():
            conn = self._networkmanager.get_connection(addr)
            conn.print_connection_stats(logging.INFO)
            if self._all_players.has(addr):
                player_data = self._all_players.get(addr)
                if self._controller.entity_is_alive(player_data.id):
                    logger.info('\t{}: {}'.format(
                        player_data.id, self._controller.state._dynamic.entities[player_data.id].position))
            else:
                logger.info('\tNo associated player state!')
        logger.info('----------------WORLD-------------------')
        logger.info('\t# Static entities:  {}'.format(len(self._controller.state._static.entities)))
        logger.info('\t# Dynamic entities: {}'.format(len(self._controller.state._dynamic.entities)))
        logger.info('----------------------------------------')
        self._controller.state.collisiondetector.log_stats(logging.INFO)


    def _check_update_rate(self):
        delta = time.time() - self._update_rate_check_time
        self._update_rate_check_time = time.time()

        updates_per_sec = self.frames / delta
        net_per_sec = self.net_updates / delta

        self.frames = 0
        self.net_updates = 0

        requested_updates_per_sec = 1.0 / Server.FRAME_TIME

        if updates_per_sec + 3 < requested_updates_per_sec:
            logger.warning('Running at {} updates/sec and {} net updates/sec: problems keeping up)'.format(
                    updates_per_sec, net_per_sec))


    def on_connect(self, addr):
        if not self._all_players.has(addr):
            logger.info("Adding " + str(addr))

            player_id = self._controller.create_player(self._gametime)
            self._all_players.get(addr).id = player_id

            # init player
            data = messages.InitLevelMsg.set(player_id, self._controller.loaded_level_name()).pack()
            self._networkmanager.send_immediate(
                addr, messages.default_messages.types.INIT_LEVEL, data)

            for name in self.configs.server.all():
                msg = self._get_svar_update_msg(name)
                data = msg.pack()
                self._networkmanager.queue(
                    addr, messages.default_messages.types.SVAR_UPDATE, data)

        else:
            logger.error("error! player at {} already exists!".format(addr))


    def on_disconnect(self, addr):
        if self._all_players.has(addr):
            logger.info('Dropping {}'.format(addr))
            player_data = self._all_players.get(addr)
            self._controller.remove_player(player_data.id, self._gametime)
            self._all_players.remove(addr)
        else:
            logger.info("error! player at {} does not exist!".format(addr))


    def run(self):
        accumulator = 0
        t = 0
        last_time = time.time()

        while 1:
            current_time = time.time()
            frame_time = current_time - last_time
            if(frame_time > 0.5):
                frame_time = 0.5

            last_time = current_time
            accumulator += frame_time

            # send update to all players
            self._sent_client_updates()

            self._networkmanager.update()
            self.net_updates += 1

            # log server state
            if time.time() - self._log_time > 10.0:
                self._log()

            if time.time() - self._update_rate_check_time > 1.0:
                self._check_update_rate()

            # while we are behind, do state update
            while accumulator > Server.FRAME_TIME:
                self.frames += 1
                self._controller.update_shared(t, Server.FRAME_TIME)
                self._controller.update(t, Server.FRAME_TIME)
                self._gametime += Server.FRAME_TIME
                t += Server.FRAME_TIME
                accumulator -= Server.FRAME_TIME

            elapsed = time.time() - current_time

            # sleep for the rest of the frame
            sleep_time = Server.FRAME_TIME - elapsed

            if sleep_time > 0.0:
                time.sleep(sleep_time)


    def _sent_client_updates(self):
        for addr in self._networkmanager.connected_peers():
            player_data = self._all_players.get(addr)
            conn = self._networkmanager.get_connection(addr)
            if time.time() - conn.last_packet_send_time > self._send_interval(conn):
                self._networkmanager.queue(
                    addr,
                    messages.default_messages.types.TIMESTAMP,
                    messages.TimestampMsg.set(self._gametime).pack())

                msgs = gamestate.LifeMessages()

                entities = set(self._controller.state._dynamic.entities.iterkeys())

                life_msgs = entities ^ player_data.last_update_entity_set

                for e in life_msgs:
                    event = self._controller._events.events[e]
                    holder = gamestate.LifeMsgHolder(
                        event[2], event[0])
                    if e in entities: # life
                        msgs.births[e] = holder
                    else: # death
                        msgs.deaths[e] = holder

                update_msg = messages.GamestateUpdateMsg.set(player_data.last_input_acks,
                                                             self._controller.state._dynamic,
                                                             msgs)
                data = update_msg.pack()

                self._networkmanager.queue(
                    addr, messages.default_messages.types.GAMESTATE_UPDATE, data)
                self._networkmanager.send_all(addr)

                player_data.last_update_time = self._gametime
                player_data.last_update_entity_set = entities
