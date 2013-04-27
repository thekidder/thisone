import logging


logger = logging.getLogger(__name__)

class ConfigVar(object):
    def __init__(self, default_value):
        self._set_internal(default_value)


    def get(self):
        return self.value


    def _set_internal(self, value):
        self.value = value


    def set(self, value):
        if self.is_valid(value):
            self._set_internal(self.convert(value))
            return True
        else:
            logger.warning(self.valid_values())
            return False



class TypedVar(ConfigVar):
    def __init__(self, default_value):
        self._type = type(default_value)
        super(TypedVar, self).__init__(default_value)


    def convert(self, value):
        return self._type(value)


    def is_valid(self, value):
        try:
            self.convert(value) # ensure we can convert to correct type
            return True
        except TypeError:
            pass
        return False


    def valid_values(self):
        return 'please input a {}'.format(self._type)



class RangeVar(TypedVar):
    def __init__(self, default_value, min_value, max_value):
        '''min and max values are inclusive'''
        self.min = min_value
        self.max = max_value
        super(RangeVar, self).__init__(default_value)


    def is_valid(self, value):
        if super(RangeVar, self).is_valid(value):
            v = self.convert(value)
            return v >= self.min and v <= self.max
        return False


    def valid_values(self):
        return 'valid numbers are between {} - {}'.format(self.min, self.max)



class OptionVar(TypedVar):
    def __init__(self, default_value, options):
        self.options = options
        super(OptionVar, self).__init__(default_value)


    def is_valid(self, value):
        if super(OptionVar, self).is_valid(value):
            v = self.convert(value)
            return v in self.options
        return False


    def valid_values(self):
        return 'valid options are {}'.format(self.options)



class BooleanVar(ConfigVar):
    TRUTH = ['yes', 'true', 't', '1']
    FALSE = ['no', 'false', 'f', '0']

    def __init__(self, default_value):
        super(BooleanVar, self).__init__(default_value)


    def convert(self, value):
        return value.lower() in BooleanVar.TRUTH


    def is_valid(self, value):
        v = value.lower()
        return v in BooleanVar.TRUTH or v in BooleanVar.FALSE


    def valid_values(self):
        return 'valid options are true and false'



class Config(object):
    def __init__(self):
        self._vars = dict()


    def all(self):
        return self._vars.iterkeys()


    def add(self, name, obj):
        self._vars[name] = obj


    def has(self, var):
        return var in self._vars


    def get(self, var):
        return self._vars[var].get()


    def obj(self, var):
        return self._vars[var]


    def set(self, var, value):
        return self._vars[var].set(value)


    def is_valid(self, var, value):
        return self._vars[var].is_valid(value)



class GameConfigs(object):
    def __init__(self, server, client):
        self.server = server
        self.client = client


    def add_cvar(self, name, obj):
        if self.client is not None:
            self.client.add_var(name, obj)


    def add_svar(self, name, obj):
        if self.server is not None:
            self.server.add_var(name, obj)


    # Commands

    def add_commands(self, command_runner):
        if self.server is not None:
            command_runner.add_local('svars', self.dump_svars)
            command_runner.add_local('get_svar', self._get_svar)
            # don't include set_svar: has different implementations in client/server

        if self.client is not None:
            command_runner.add_local('cvars', self.dump_cvars)
            command_runner.add_local('get_cvar', self._get_cvar)
            command_runner.add_local('set_cvar', self._set_cvar)


    def set_svar(self, args):
        if len(args) != 2:
            logger.warning('invalid number of arguments to set_svar')
        else:
            self.server.set(args[0], args[1])


    def dump_all(self):
        self.dump_cvars()
        self.dump_svars()


    def dump_cvars(self, args=None):
        logger.info('Printing all cvars:')
        if self.client is not None:
            for k in self.client.all():
                self._get_cvar([k])


    def dump_svars(self, args=None):
        logger.info('Printing all svars:')
        if self.server is not None:
            for k in self.server.all():
                self._get_svar([k])


    def _get_cvar(self, args):
        if len(args) != 1:
            logger.warning('invalid number of arguments to get_cvar')
        else:
            logger.info('cvar {} = {}'.format(args[0], self.client.get(args[0])))


    def _get_svar(self, args):
        if len(args) != 1:
            logger.warning('invalid number of arguments to get_svar')
        else:
            logger.info('svar {} = {}'.format(args[0], self.server.get(args[0])))


    def _set_cvar(self, args):
        if len(args) != 2:
            logger.warning('invalid number of arguments to set_cvar')
        else:
            self.client.set(args[0], args[1])


    def _check_client(self, fn):
        def wrapped():
            if self.client is None:
                logger.warning('no cvars object')
                return
            else:
                return fn()
        return wrapped()


    def _check_server(self, fn):
        def wrapped():
            if self.server is None:
                logger.warning('no svars object')
                return
            else:
                return fn()
        return wrapped()
