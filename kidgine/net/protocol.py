import hashlib

# builds a hash of "protocol name + protocol version" and uses the
# hash of the first few bytes as protocol identifier.

_hashfunc = hashlib.sha256
_hashsize = 4 * 8 # use first 4 bytes of hash for protocol header

_mask = 1 << _hashsize
_mask -= 1

class Protocol(object):
    def __init__(self, name, version, compatible_versions):
        self.name = name
        self._version = version
        self.compatible_versions = list(compatible_versions)
        self.compatible_versions.append(version)
        self._protocol_cache = dict()

        self._build_protocol_cache()


    def _protocol_hash(self, version):
        hash = _hashfunc(self.name + str(version))
        digest = int(hash.hexdigest(), 16)
        digest = digest & _mask # get first _hashsize bytes
        return digest


    def _build_protocol_cache(self):
        for version in self.compatible_versions:
            self._protocol_cache[self._protocol_hash(version)] = version


    def is_valid(self, header_id):
        return header_id in self._protocol_cache


    def version(self, header_id):
        if not self.is_valid(header_id):
            return None
        return self._protocol_cache[header_id]


    def latest_version(self):
        return self._protocol_hash(self._version)
