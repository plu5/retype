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


def isspace(s):
    """
    Extension of str.isspace that also checks for other unicode characters that
    are effectively space.
    """
    if s.isspace():
        return True
    for char in s:
        if not char.isspace() and char not in effectively_space:
            return False
    return True


def isspaceorempty(s):
    if isspace(s) or s == '':
        return True
    return False


def spacerstrip(s):
    def _spacerstrip(s):
        return s.rstrip().rstrip(''.join(effectively_space))
    s = _spacerstrip(s)
    while s != _spacerstrip(s):
        s = _spacerstrip(s)
    return s
