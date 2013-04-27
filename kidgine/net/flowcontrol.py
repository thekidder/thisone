import logging
import time
from ..math import clamp


# time between each heartbeat packet
HEARTBEAT_TIME = 0.1

logger = logging.getLogger(__name__)

class BinaryFlowControl(object):
    # in seconds
    MAX_TIME_BETWEEN_PACKETS = HEARTBEAT_TIME * 2
    # in ms
    MAX_RTT = 300

    # in seconds
    MIN_HYSTERESIS   = 1
    MAX_HYSTERESIS   = 60
    HYSTERESIS_START = 10

    def __init__(self):
        self.net_rtt = 0
        self.time_since_last_packet = time.time()
        self.good = True
        self.last_mode_change = time.time()
        self.last_hysteresis_change = time.time()
        self.hysteresis = BinaryFlowControl.HYSTERESIS_START
        self.good_since = time.time()


    def update(self, net_rtt, time_since_last_packet):
        self.net_rtt = net_rtt
        self.time_since_last_packet = time_since_last_packet

        # are conditions good?
        currently_good = self.is_good()
        if not currently_good:
            self.good_since = time.time()

        # are things bad now?
        if self.good and not currently_good:
            logger.info('switching to bad mode')
            logger.info('rtt: {}; time since last packet: {}'.format(
                self.net_rtt, self.time_since_last_packet))
            self.good = False
            if time.time() - self.last_mode_change < self.hysteresis:
                self.hysteresis = clamp(
                    self.hysteresis * 2,
                    BinaryFlowControl.MIN_HYSTERESIS,
                    BinaryFlowControl.MAX_HYSTERESIS)
                self.last_hysteresis_change = time.time()
            self.last_mode_change = time.time()

        # have conditions been good for long enough?
        if not self.good and time.time() - self.good_since > self.hysteresis:
            logger.info('switching to good mode')
            self.good = True
            self.last_mode_change = time.time()

        if self.good and time.time() - self.last_hysteresis_change > 10:
            self.hysteresis = clamp(
                self.hysteresis / 2,
                BinaryFlowControl.MIN_HYSTERESIS,
                BinaryFlowControl.MAX_HYSTERESIS)
            self.last_hysteresis_change = time.time()


    def is_good(self):
        if (self.net_rtt > BinaryFlowControl.MAX_RTT
            or self.time_since_last_packet > BinaryFlowControl.MAX_TIME_BETWEEN_PACKETS):

            return False
        return True
