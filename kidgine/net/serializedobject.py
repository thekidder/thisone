import inspect
import logging
import struct
import types

import classtags


_DEBUG = False

# name of the attribute that classes use
_SERIALIZED_MEMBERS_ATTR_NAME = '_SERIALIZED_MEMBERS'

logger = logging.getLogger(__name__)


_classtags = None
def set_class_tags(classtags):
    global _classtags
    _classtags = classtags


class Int(object):
    def __init__(self, size=4, signed=True):
        self.size = size
        self.signed = signed

        if size == 1:
            self.structcode = 'b'
        elif size == 2:
            self.structcode = 'h'
        elif size == 4:
            self.structcode = 'i'
        elif size == 8:
            self.structcode = 'q'
        else:
            raise RuntimeError('Invalid integer size ' + str(size))

        if not signed:
            self.structcode = self.structcode.upper()


    def __str__(self):
        signed = ''
        if not self.signed:
            signed = 'u'
        return '{}int{}'.format(signed, self.size)


# aliases
char   = Int(1,signed=True)
uchar  = Int(1,signed=False)

short  = Int(2,signed=True)
ushort = Int(2,signed=False)

int    = Int(4,signed=True)
uint   = Int(4,signed=False)

long   = Int(8,signed=True)
ulong  = Int(8,signed=False)


class Float(object):
    def __init__(self, size=4):
        self.size = size

        if size == 4:
            self.structcode = 'f'
        elif size == 8:
            self.structcode = 'd'
        else:
            raise RuntimeError('Invalid float size ' + str(size))

    def __str__(self):
        if self.size == 4:
            return 'float'
        elif self.size == 8:
            return 'double'
        else:
            return 'float ({})'.format(self.size)


class String(object):
    def __init__(self, size):
        self.size = size

        self.structcode = str(size) + 'p'


    def __str__(self):
        return 'string ({})'.format(self.size)


# aliases
float  = Float(4)
double = Float(8)


class Bool(object):
    def __init__(self):
        self.size = 1
        self.structcode = '?'

    def __str__(self):
        return 'bool'


bool = Bool()


def CreateBitfield(**kwargs):
    class _BitfieldMetaclass(_SerializedObjectMetaclass):
        def __new__(cls, name, bases, dct):
            dct[_SERIALIZED_MEMBERS_ATTR_NAME] = dict()
            for i in range((len(kwargs) + 7) / 8):
                name = 'byte{}'.format(i)
                dct[name] = 0
                dct[_SERIALIZED_MEMBERS_ATTR_NAME][name] = uchar

            def _get(pos, index):
                name = 'byte{}'.format(pos)
                def wrapper(self):
                    return getattr(self, name) & (1 << index) != 0
                return wrapper

            def _set(pos, index):
                name = 'byte{}'.format(pos)
                def wrapper(self, value):
                    value = 1 if value else 0
                    existing = getattr(self, name)
                    if value:
                        setattr(self, name, (1 << index) | existing)
                    else:
                        setattr(self, name, ~(1 << index) & existing)
                return wrapper

            for i,(k,v) in enumerate(sorted(kwargs.iteritems())):
                pos = i / 8
                index = i % 8
                dct[k] = property(_get(pos, index), _set(pos, index))


            c = super(_BitfieldMetaclass, cls).__new__(cls, name, bases, dct)
            return c

    class _Bitfield(SerializedObject):
        __metaclass__ = _BitfieldMetaclass

        def __init__(self):
            for k,v in kwargs.iteritems():
                setattr(self, k, v)

    return _Bitfield


MAX_LEN_255 = 1
MAX_LEN_65535 = 2
MAX_LEN_4_BILLION = 4

class Array(object):
    def __init__(self, object_type, max_len_bytes):
        super(Array, self).__init__()
        self._type = object_type
        acceptable_len_bytes = [1, 2, 4]
        if max_len_bytes not in acceptable_len_bytes:
            raise RuntimeError('Invalid maximum array length')
        self.max_len_bytes = max_len_bytes


    def create(self):
        return list()


    def unpack_item(self, data):
        """returns item, remaining data"""
        x,data = self._type()._create(data)
        if x is not None:
            data = x.unpack(data)
        return x,data


    def add(self, container, item):
        container.append(item)


    def iterator(self, container):
        return container


    def packer_type(self):
        return self._type


    def __str__(self):
        return 'array of {} (max len 2^{:<2}-1)'.format(self._type, self.max_len_bytes*8)



class Dict(object):
    def __init__(self, key_type, value_type, max_len_bytes):
        super(Dict, self).__init__()
        self._key_type = key_type
        self._value_type = value_type
        self._type = _DictHolder(self._key_type, self._value_type)
        acceptable_len_bytes = [1, 2, 4]
        if max_len_bytes not in acceptable_len_bytes:
            raise RuntimeError('Invalid maximum dict length')
        self.max_len_bytes = max_len_bytes


    def create(self):
        return dict()


    def unpack_item(self, data):
        obj = self._type()
        data = obj.unpack(data)
        return obj,data


    def add(self, container, item):
        container[item.key] = item.value


    def iterator(self, container):
        for k,v in container.iteritems():
            obj = self._type()
            obj.key = k
            obj.value = v
            yield obj


    def packer_type(self):
        return self._type


    def __str__(self):
        return 'dict of {}, {} (max len 2^{:<2}-1)'.format(
            self._key_type, self._value_type, self.max_len_bytes*8)



def _DictHolder(key_type, value_type):
    # what we are doing here is way too clever. we serialize dicts by
    # creating a holder which is responsible for serializing the key,
    # value pair for each entry. on serialization, we loop through the
    # dict and create a holder for each item. on deserialization, we
    # create a holder, unpack into it, and use this to construct the
    # dict again.

    # The holder has to be a metaclass because the serialization dict
    # is dynamic. We construct this here. This is derived from
    # _SerializedObjectMetaclass, so once we create the dict, we pass
    # it on to that metaclass. This creates a type for us that holds
    # the key, value pair.
    class _DictHolderMetaclass(_SerializedObjectMetaclass):
        def __new__(cls, name, bases, dct):
            dct[_SERIALIZED_MEMBERS_ATTR_NAME] = {
                'key'   : key_type,
                'value' : value_type }

            c = super(_DictHolderMetaclass, cls).__new__(cls, name, bases, dct)
            return c

    class _DictHolderClass(SerializedObject):
        __metaclass__ = _DictHolderMetaclass

    return _DictHolderClass



_polymorphic_packer = struct.Struct('!B')

class Polymorphic(object):
    static_size = 0

    def __init__(self):
        super(Polymorphic, self).__init__()


    def _create(self, data):
        [key] = _polymorphic_packer.unpack(data[:_polymorphic_packer.size])
        data = data[_polymorphic_packer.size:]
        cls = _classtags.tag_to_class(key)

        if _DEBUG:
            logger.info('unpacking polymorphic: got tag {} corresponding to {}'.format(
                    key, cls))

        if isinstance(cls(), classtags.NoneType):
            obj = None
        else:
            obj = cls()

        return [obj, data]



class _SerializedObjectMetaclass(type):
    def __new__(cls, name, bases, dct):
        if name != 'SerializedObject':
            # only do things if initializing a subclass of SerializedObject
            dct = _SerializedObjectMetaclass.create(cls, name, bases, dct)
        return super(_SerializedObjectMetaclass, cls).__new__(cls, name, bases, dct)


    @staticmethod
    def create(cls, name, bases, dct):
        if not _SERIALIZED_MEMBERS_ATTR_NAME in dct:
            raise RuntimeError(
                'Need an attribute called {} in {}'.format(_SERIALIZED_MEMBERS_ATTR_NAME, name))

        format_str = '!'
        format_str_arr = ''
        serialized_members = list()

        serialized_packable_members = list()
        additional_size = 0

        serialized_array_members = list()

        for attr_name in sorted(dct[_SERIALIZED_MEMBERS_ATTR_NAME].iterkeys()):
            datatype = dct[_SERIALIZED_MEMBERS_ATTR_NAME][attr_name]
            if isinstance(datatype, types.StringType):
                # string, interpret as code for struct format string
                serialized_members.append(attr_name)
                format_str += datatype
            elif hasattr(datatype, 'structcode'):
                # use object.structcode for format str
                serialized_members.append(attr_name)
                format_str += datatype.structcode
            elif hasattr(datatype, 'unpack_item'): # assume it's some sort of sequence type
                serialized_array_members.append((attr_name,datatype))
                additional_size += datatype.max_len_bytes
                format_str_arr += Int(datatype.max_len_bytes, False).structcode
            else:
                # custom object, assume it implements serializedobject interface
                serialized_packable_members.append((attr_name,datatype))
                additional_size += datatype.static_size

        format_str += format_str_arr

        _packer = struct.Struct(format_str)
        dct['_packer'] = _packer
        # static size is the serialized size (disregarding arrays of variable size)
        dct['static_size'] = _packer.size + additional_size
        dct['serialized_members'] = serialized_members
        dct['serialized_packable_members'] = serialized_packable_members
        dct['serialized_array_members'] = serialized_array_members

        return dct



class SerializedObject(object):
    __metaclass__ = _SerializedObjectMetaclass

    def __init__(self):
        pass


    def _create(self, data):
        return [self.__class__(), data]


    def pack(self, top=True, level=''):
        try:
            fn = self.before_pack
        except AttributeError:
            pass # guess there's no before_pack
        else:
            fn()
        items = list()
        for name in self.serialized_members:
            items.append(getattr(self, name))

        # serialize array sizes
        for name,datatype in self.serialized_array_members:
            items.append(len(getattr(self, name)))

        packed_str = ''
        if len(items) > 0:
            packed_str = self._packer.pack(*items)

        def print_type(actual, declared, name):
            # assume primitive type
            if not inspect.isclass(declared):
                packed_member_log[name] += '{}    Primitive type: {}\n'.format(level, declared)
                return

            if isinstance(declared(), Polymorphic):
                packed_member_log[name] += '{}    Resolved type: {}\n'.format(
                    level, type(actual))
            elif not isinstance(actual, declared) or not isinstance(declared(), type(actual)):
                s = '{}    Actual type {} differs from non-polymorphic type {}!\n'.format(
                    level, type(actual), declared)
                packed_member_log[name] += s
            else:
                packed_member_log[name] += '{}    {}\n'.format(level, type(actual))

        def pack_obj(name, datatype, obj):
            data = ''
            if inspect.isclass(datatype) and isinstance(datatype(), Polymorphic):
                if obj == None:
                    data += _polymorphic_packer.pack(_classtags.class_to_tag(classtags.NoneType))
                else:
                    data += _polymorphic_packer.pack(_classtags.class_to_tag(obj.__class__))

            print_type(obj, datatype, name)
            if inspect.isclass(datatype) and isinstance(datatype(), Polymorphic):
                packed_member_log[name] += '{}    {:<4} Polymorphic class type header\n'.format(
                    level, _polymorphic_packer.size)
            if obj != None:
                data += obj.pack(False,level+'    ')
            if _DEBUG:
                packed_member_log[name] += obj.packed_log()
            packed_member_size[name] += len(data)
            return data

        packed_member_log = dict()
        packed_member_size = dict()
        obj_size = len(packed_str)
        for name,datatype in self.serialized_packable_members:
            packed_member_log[name] = ''
            packed_member_size[name] = 0
            packed_str += pack_obj(name, datatype, getattr(self, name))

        obj_size = len(packed_str) - obj_size

        arr_size = len(packed_str)
        for name,datatype in self.serialized_array_members:
            packed_member_log[name] = ''
            packed_member_size[name] = 0
            for item in datatype.iterator(getattr(self, name)):
                packed_str += pack_obj(name, datatype.packer_type(), item)

        arr_size = len(packed_str) - arr_size

        if _DEBUG:
            self._packed_log = ''
            if top:
                self._packed_log += '{}Packed an instance of {}\n'.format(level, self.__class__)

            array_len_size = 0
            primitive_size = self._packer.size
            for name,datatype in self.serialized_array_members:
                # array sizes are included in packer, subtract to get actual count
                dct = getattr(self, _SERIALIZED_MEMBERS_ATTR_NAME)
                primitive_size -= dct[name].max_len_bytes
                array_len_size += dct[name].max_len_bytes
            arr_size += array_len_size

            # print primitives
            if primitive_size > 0:
                self._packed_log += '{}{:<4} Primitives:\n'.format(level, primitive_size)
                for name in self.serialized_members:
                    dct = getattr(self, _SERIALIZED_MEMBERS_ATTR_NAME)
                    self._packed_log += '{}  {:<4} {:18}: {}\n'.format(
                        level, dct[name].size, name, dct[name])

            # print objects
            if obj_size > 0:
                self._packed_log += '{}{:<4} Objects:\n'.format(level, obj_size)
                for name,datatype in self.serialized_packable_members:
                    dct = getattr(self, _SERIALIZED_MEMBERS_ATTR_NAME)
                    s = '{}  {:<4} {}: {}\n'.format(
                        level, packed_member_size[name], name, dct[name])
                    self._packed_log += s
                    try:
                        self._packed_log += '{:<4}'.format(packed_member_log[name])
                    except KeyError:
                        pass # no log

            # print arrays
            if arr_size > 0:
                self._packed_log += '{}{:<4} Arrays:\n'.format(level, arr_size)
                for name,datatype in self.serialized_array_members:
                    dct = getattr(self, _SERIALIZED_MEMBERS_ATTR_NAME)
                    size = packed_member_size[name] + dct[name].max_len_bytes
                    self._packed_log += '{}  {:<4} {}: {} (actual len {})\n'.format(
                        level, size, name, dct[name], len(getattr(self, name)))
                    s = '{}    {:<4} Array length header\n'.format(
                        level, dct[name].max_len_bytes)
                    self._packed_log += s

                    try:
                        self._packed_log += packed_member_log[name]
                    except KeyError:
                        pass # no array members

            # print summary
            self._packed_log += '{}{:<4} Total\n'.format(
                level, arr_size + obj_size + primitive_size)

            if top:
                logger.info(self._packed_log)

            assert primitive_size + obj_size + arr_size == len(packed_str)

        return packed_str


    def packed_log(self):
        return self._packed_log


    def unpack(self, data_to_unpack):
        array_sizes = list()
        if self._packer.size > 0:
            raw = self._packer.unpack(data_to_unpack[:self._packer.size])

            i = 0
            for name in self.serialized_members:
                setattr(self, name, raw[i])
                i += 1

            for name in self.serialized_array_members:
                array_sizes.append(raw[i])
                i += 1

        data = data_to_unpack[self._packer.size:]
        for name,datatype in self.serialized_packable_members:
            x,data = datatype()._create(data)
            if x != None:
                data = x.unpack(data)
            setattr(self, name, x)

        i = 0
        for name,datatype in self.serialized_array_members:
            container = datatype.create()
            for j in range(array_sizes[i]):
                if _DEBUG:
                    logger.info('unpacking {}: {}'.format(name, datatype))
                x,data = datatype.unpack_item(data)
                datatype.add(container, x)
            setattr(self, name, container)
            i += 1

        try:
            fn = self.after_unpack
        except AttributeError:
            pass
        else:
            fn()

        return data
