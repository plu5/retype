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


# Characters that are effectively space but not detected by isspace
effectively_space = ['\ufeff', '\u180e', '\u200b', '\u000a']


# Characters I hate and want to ignore even though they are not really space
garbage_characters = ['\ufffc']


def isspace(s, orgarbage=False):
    """
    Extension of str.isspace that also checks for other unicode characters that
    are effectively space.
    """
    if s.isspace():
        return True
    extra_characters = effectively_space + garbage_characters if orgarbage\
        else effectively_space
    for char in s:
        if not char.isspace() and char not in extra_characters:
            return False
    return True


def isspaceorempty(s, orgarbage=False):
    if isspace(s, orgarbage) or s == '':
        return True
    return False


def spacerstrip(s):
    def _spacerstrip(s):
        return s.rstrip().rstrip(''.join(effectively_space))
    s = _spacerstrip(s)
    while s != _spacerstrip(s):
        s = _spacerstrip(s)
    return s
