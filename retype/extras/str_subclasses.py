import logging
from copy import deepcopy
from collections import UserString


logger = logging.getLogger('str_subclasses')
# Suppress our rather verbose logs by default. They can be shown in tests by
#  setting level to DEBUG.
logger.setLevel(logging.WARNING)


class AnyStr(UserString):
    """A string that is equal to all `possibilities'. Each possibility
 should be equal in length."""
    def __init__(self, *possibilities):
        super().__init__(possibilities[0])
        self.base = possibilities[0]
        self.possibilities = possibilities

    def __eq__(self, s):
        if s in self.possibilities:
            return True
        return False

    def __add__(self, s):
        if isinstance(s, str):
            return AnyStr(*[possibility + s for possibility
                            in self.possibilities])
        if isinstance(s, AnyStr):
            if len(s.possibilities) != len(self.possibilities):
                raise ValueError("can only concatenate AnyStr to AnyStr if they\
 have the same number of possibilities (not {} and {})"
                                 .format(len(self.possibilities),
                                         len(s.possibilities)))
            return AnyStr(*[self.possibilities[i] + s.possibilities[i]
                            for i in range(len(self.possibilities))])
        else:
            raise TypeError('can only concatenate str or AnyStr (not "{}")\
 to AnyStr'.format(type(s)))

    def join(self, iterable):
        """Not like the str method because we don’t put anything in between"""
        result = None
        for s in iterable:
            if not result:
                result = s
            else:
                result += s
        return result

    def __getitem__(self, i):
        if isinstance(i, int):
            if i < 0:
                self.__getitem__(len(self.base) + i)
            return AnyStr(*[possibility[i] for possibility
                            in self.possibilities])
        elif isinstance(i, slice):
            start, stop, step = i.indices(len(self))
            return self.join([self[j] for j in range(start, stop, step)])
        else:
            raise TypeError("AnyStr indices must be integers or slices, not {}"
                            .format(type(i)))

    def __str__(self):
        # this is kind of weird but i am doing this for ease of use in manifold
        #  when we calculate combined. but it isn’t ideal, returning self.base
        #  would make more sense (but break our usage in manifold)
        if len(self.possibilities) > 1:
            return str(self.possibilities[1])
        else:
            return str(self.base)

    def strip(self, chars=" ", directions=[1, -1]):
        new = AnyStr(*self.possibilities)
        for i in directions:
            if i == 1:
                sl = slice(i, 0)
                k = 0
            elif i == -1:
                sl = slice(0, i)
                k = -1
            else:
                raise ValueError("each direction is expected to be 1 or -1, \
not {}".format(i))
            for char in chars:
                while new and new[k] == char:
                    new = new[sl]
                    if new is None:
                        new = ''
                        break
        return new

    def lstrip(self, chars=" "):
        return self.strip(chars, directions=[1])

    def rstrip(self, chars=" "):
        return self.strip(chars, directions=[-1])

    def isspace(self):
        if self.strip() == '':
            return True
        return False


class ManifoldStr(UserString):
    def __init__(self, data, rdict):
        """A string structure that takes an str `data' and a dictionary
 `rdict' where each key is a substring to be replaced, and
 corresponding value is an array of possible replacements of equal length. Each
 key in `replacement_dict' is replaced where found in `data' with an AnyStr
 containing key and replacements."""
        super().__init__(data)
        self.base = data
        self.rdict = rdict
        # A dictionary of strs and AnyStrs with the index of where each begins
        self.manifold = {0: data}

        def makeCombined():
            keys = sorted([*self.manifold])
            combined = ''.join([str(self.manifold[key]) for key in keys])
            return combined

        logger.debug("Initialisation start. Initial value of manifold: {}"
                     .format(self.manifold))

        for replace_me, replacements in rdict.items():
            logger.debug('--- New iteration on replacements loop ---')
            logger.debug("Current replace: '{}'".format(replace_me))
            logger.debug('Current value of manifold: {}'.format(self.manifold))
            combined = makeCombined()
            logger.debug("Searching through combined: '{}'".format(combined))
            index = combined.find(replace_me)
            logger.debug("First find at index: {}".format(index))
            while index != -1:
                manifold_copy = deepcopy(self.manifold)
                # Go through the substrings that are at or before our position
                for i, substring in manifold_copy.items():
                    if i > index:
                        continue
                    # Skip if it is an AnyStr, thus already had a replacement;
                    #  nothing we can do
                    if type(substring) is not str:
                        continue

                    logger.debug("Looking at substring: {} '{}'"
                                 .format(i, substring))

                    del self.manifold[i]

                    before_us = substring[:index - i]
                    logger.debug("before us: '{}'".format(before_us))
                    if before_us:
                        self.manifold[i] = before_us

                    after_us = substring[len(before_us) + len(replace_me):]
                    logger.debug("after us: '{}'".format(after_us))
                    if after_us:
                        new_key = index + len(replace_me)
                        self.manifold[new_key] = after_us

                # Place new AnyStr
                self.manifold[index] = AnyStr(replace_me, *replacements)

                # Construct new string to search through for what still needs
                #  replacing
                combined = makeCombined()
                logger.debug("New combined: '{}'".format(combined))
                index = combined.find(replace_me)
                logger.debug("Next index: {}".format(index))

        logger.debug("Initialisation complete. Final value of manifold: {}\n"
                     .format(self.manifold))

    def __eq__(self, s):
        if s == self.data:
            return True
        else:  # else check against substrings
            for i, substring in self.manifold.items():
                if s[i: i + len(substring)] != substring:
                    return False
            return True
        return False

    def __add__(self, s):
        if isinstance(s, str):
            return ManifoldStr(self.base + s, self.rdict)
        if isinstance(s, AnyStr):
            new_rdict = deepcopy(self.rdict)
            new_rdict[s.base] = s.possibilities[1:]
            return ManifoldStr(self.base + s.base, new_rdict)
        if isinstance(s, ManifoldStr):
            new_rdict = deepcopy(self.rdict)
            for k, v in s.rdict.items():
                new_rdict[k] = v
            return ManifoldStr(self.base + s.base, new_rdict)
        else:
            raise TypeError('can only concatenate str, AnyStr, or ManifoldStr\
 (not "{}") to ManifoldStr'.format(type(s)))

    def join(self, iterable):
        result = None
        for s in iterable:
            if not result:
                result = s
            else:
                result += s
        return result

    def __getitem__(self, i):
        if isinstance(i, int):
            if i < 0:
                return self.__getitem__(len(self.data) + i)
            elif i in self.manifold:
                return self.manifold[i][0]
            else:
                # Find substring before i, and extract just the index required
                descending_keys = sorted([*self.manifold], reverse=True)
                substring = None
                for k in descending_keys:
                    if k < i:
                        substring, k = (self.manifold[k], k)
                        break
                if substring is None:
                    raise KeyError
                return substring[i - k]
        elif isinstance(i, slice):
            start, stop, step = i.indices(len(self))
            return self.join([self[j] for j in range(start, stop, step)])
        else:
            raise TypeError("ManifoldStr indices must be integers or slices,\
 not {}".format(type(i)))

    def strip(self, chars=" ", directions=[1, -1]):
        new = deepcopy(self)
        for i in directions:
            if i == 1:
                sl = slice(i, 0)
                k = 0
            elif i == -1:
                sl = slice(0, i)
                k = -1
            else:
                raise ValueError("each direction is expected to be 1 or -1, \
not {}".format(i))
            for char in chars:
                while new and new[k] == char:
                    new = new[sl]
                    if new is None:
                        new = ''
                        break
        return new

    def lstrip(self, chars=" "):
        return self.strip(chars, directions=[1])

    def rstrip(self, chars=" "):
        return self.strip(chars, directions=[-1])

    def isspace(self):
        if self.strip() == '':
            return True
        return False
