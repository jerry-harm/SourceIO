import json
from pathlib import Path
from .murmurhash2 import murmur_hash2

MURMUR2SEED = 0x31415926


class EntityKeyValuesKeys:
    _json_path = (Path(__file__).parent / 'entitykeyvalues_strings.json')
    _raw_strings_path = (Path(__file__).parent / 'entitykeyvalues_strings.txt')
    lookup_table = {}
    _all_keys = []

    def __init__(self):
        if not self.lookup_table:
            if self._json_path.exists():
                with self._json_path.open('r') as file:
                    self.lookup_table = {int(key): value for key, value in json.load(file).items()}
            else:
                with self._raw_strings_path.open('r') as file:
                    self._all_keys = file.readlines()
                self.precompute_keys()
                with self._json_path.open('w') as file:
                    json.dump(self.lookup_table, file)

    def precompute_keys(self):
        for skey in self._all_keys:
            skey = skey.strip('\n')
            if skey in self.lookup_table.values():
                continue
            mhash = murmur_hash2(skey, MURMUR2SEED)
            self.lookup_table[mhash] = skey

    def get(self, key_hash):
        return self.lookup_table.get(key_hash, key_hash)
