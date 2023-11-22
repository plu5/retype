import collections.abc


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
    def __init__(self, base_dict, fallback_dict={}, parent_keys=[]):
        self.raw = base_dict
        self.fallback = fallback_dict
        self.parent_keys = parent_keys

    def __getitem__(self, key, default=None):
        r = self.raw.get(key, self.fallback.get(key, default))
        if type(r) == dict and key not in self.parent_keys:
            return _NestedSafeDictGroup(key, r, self.fallback)
        return r

    def get(self, key, default=None):
        return self.__getitem__(key, default)


class _NestedSafeDictGroup:
    def __init__(self, name, group, fallback_dict={}):
        self.name = name
        self.group = group
        self.fallback = fallback_dict

    def __getitem__(self, key, default=None):
        return self.group.get(
            key, self.fallback[self.name].get(key, default))

    def get(self, key, default=None):
        return self.__getitem__(key, default)
