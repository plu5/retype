import collections.abc
from copy import deepcopy


def update(source, overrides):
    # by charlax, https://stackoverflow.com/a/30655448
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, collections.abc.Mapping) and value:
            returned = update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source


class SafeDict:
    def __init__(self, base_dict, fallback_dict={}, nested_raw_dict_keys=[]):
        self.raw = base_dict
        self.fallback = fallback_dict
        self.nested_raw_dict_keys = nested_raw_dict_keys

    def __getitem__(self, key, default=None):
        r = self.raw.get(key, self.fallback.get(key, default))
        if type(r) == dict and key not in self.nested_raw_dict_keys:
            return _NestedSafeDictGroup(key, r, self.fallback)
        return r

    def __setitem__(self, key, value):
        if type(value) == dict and key in self.nested_raw_dict_keys:
            self.raw.setdefault(key, _NestedSafeDictGroup(
                key, value, self.fallback))
        else:
            self.raw[key] = value

    def get(self, key, default=None):
        return self.__getitem__(key, default)

    def update(self, overrides):
        self.raw = update(self.raw, overrides)

    def deepcopy(self):
        return SafeDict(deepcopy(self.raw), self.fallback,
                        self.nested_raw_dict_keys)

    def values(self):
        return self.raw.values()

    def items(self):
        return self.raw.items()


class _NestedSafeDictGroup:
    def __init__(self, name, group, fallback_dict={}):
        self.name = name
        self.raw = self.group = group
        self.fallback = fallback_dict

    def __getitem__(self, key, default=None):
        return self.group.get(
            key, self.fallback.get(self.name, {}).get(key, default))

    def __setitem__(self, key, value):
        self.raw[key] = value

    def get(self, key, default=None):
        return self.__getitem__(key, default)

    def update(self, overrides):
        self.raw = update(self.raw, overrides)

    def values(self):
        return self.raw.values()

    def items(self):
        return self.raw.items()
