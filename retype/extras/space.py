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
    ns = _spacerstrip(s)
    while ns != _spacerstrip(ns):
        ns = _spacerstrip(ns)
    return ns


def nspacerstrip(s):
    ns = s
    if len(s) and s[-1] == '\n':
        ns = spacerstrip(s[0:-1])
    return ns


def nrspacerstrip(s):
    ns = nspacerstrip(s)
    while len(ns) and ns[-1] == '\r':
        ns = s[0:-1]
    return ns

def endsinn(s):
    if len(s) and s[-1] == '\n':
        return True
    return False
