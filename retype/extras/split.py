from copy import deepcopy


# https://docs.python.org/3/library/stdtypes.html#str.splitlines
newlines = ['\r\n', '\n', '\r', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x85',
            '\u2028', '\u2029']


def isnewline(s):
    return s in newlines


def splittext(text, sdict, indicatenewlines=False, finalnewline=False,
              fill=None):
    """Split text according to splitters in sdict.
sdict structure:
{'substr1': {'keep': True}, 'substr2': {'keep': False}, ...}
where 'keep' is whether the splitter should stay in the text (like splitlines'\
 keepends argument).
If 'indicatenewlines' is True, newline splitters will by replaced by \\n.
If 'finalnewline' is True, the final item in the resulting list will have \\n\
 appended to the end of it.
'fill' is an optional character to add to the end of each item when 'keep' is\
 False to compensate for the length of the splitter in order to keep the\
 length of the overall text the same (except for the final item)."""
    res = []
    sdict = deepcopy(sdict)
    remaining = list(sdict)
    i = n = 0
    while len(remaining):
        s = remaining[n]
        pos = text.find(s, i)
        if pos < 0:
            del remaining[n]
        else:
            sdict[s]['pos'] = pos+len(s) if sdict[s]['keep'] else pos
            n += 1
        if len(remaining) and n >= len(remaining):
            nearest_s = min(remaining, key=lambda s: sdict[s]['pos'])
            pos = sdict[nearest_s]['pos']
            keep = sdict[nearest_s]['keep']
            item = text[i:pos]
            if indicatenewlines and isnewline(nearest_s):
                item += '\n'
            elif fill and not keep:
                item += fill * len(nearest_s)
            res.append(item)
            i = pos if keep else pos+len(nearest_s)
            n = 0
    item = text[i:len(text)]
    if finalnewline:
        item += '\n'
    res.append(item)
    return res
