import logging
from copy import deepcopy
from collections import UserString

from typing import TYPE_CHECKING


logger = logging.getLogger('str_subclasses')
# Suppress our rather verbose logs by default. They can be shown in tests by
#  setting level to DEBUG.
logger.setLevel(logging.WARNING)


class AnyStr(UserString):
    """A string that is equal to all `possibilities'. Each possibility
 should be equal in length."""
    def __init__(self, *possibilities):
        # type: (AnyStr, str) -> None
        super().__init__(possibilities[0])
        self.base = possibilities[0]
        self.possibilities = []  # type: list[str]

        # Get rid of duplicate possibilities
        for possibility in possibilities:
            if possibility not in self.possibilities:
                self.possibilities.append(possibility)

    def __eq__(self, s):
        # type: (AnyStr, object) -> bool
        if s in self.possibilities:
            return True
        return False

    def _add(self, s, order=1):
        # type: (AnyStr, object, int) -> ManifoldStr
        args = None  # type: None | tuple[object, object]
        if order == 1:
            args = (self, s)
        elif order == -1:
            args = (s, self)
        else:
            raise ValueError("order is expected to be 1 or -1, not {}"
                             .format(order))

        if isinstance(s, str):
            return ManifoldStr.from_str_and_anystr(s, self, -order)
        if isinstance(s, AnyStr):
            return ManifoldStr.from_anystr_and_anystr(*args)
        else:
            return NotImplemented  # type: ignore[no-any-return]
            # raise TypeError('can only concatenate str or AnyStr (not "{}")\
# to AnyStr'.format(type(s)))

    def __add__(self, s):  # type: ignore[override]
        # type: (AnyStr, object) -> ManifoldStr
        return self._add(s, 1)

    def __radd__(self, s):  # type: ignore[override]
        # type: (AnyStr, object) -> ManifoldStr
        return self._add(s, -1)

    def join(self, iterable):  # type: ignore[override]
        # type: (AnyStr, Iterable[str | UserString]) -> str | UserString
        """Not like the str method because we don’t put anything in between"""
        result = ''  # type: str | UserString
        for s in iterable:
            if not result:
                result = s
            else:
                result += s
        return result

    def __getitem__(self, i):  # type: ignore[override]
        # type: (AnyStr, IndexOrSlice) -> AnyStr | str
        if isinstance(i, int):
            if i < 0:
                self.__getitem__(len(self.base) + i)
            return AnyStr(*[possibility[i] for possibility
                            in self.possibilities])
        elif isinstance(i, slice):  # type: ignore[misc]  # slice[Any, ...]
            start, stop, step = i.indices(len(self))
            if step == 1 and start == 0 and stop == len(self):
                return self
            # Breaking up AnyStrs is unsupported, revert to str
            else:
                logger.debug("__getitem__ call that breaks up an AnyStr")
                return ''.join([self.base[j] for j
                                in range(start, stop, step)])
        else:
            raise TypeError("AnyStr indices must be integers or slices, not {}"
                            .format(type(i)))

    def __str__(self):
        # type: (AnyStr) -> str
        # this is kind of weird but i am doing this for ease of use in manifold
        #  when we calculate combined. but it isn’t ideal, returning self.base
        #  would make more sense (but break our usage in manifold)
        if len(self.possibilities) > 1:
            return str(self.possibilities[1])
        else:
            return str(self.base)

    def __repr__(self):
        # type: (AnyStr) -> str
        return (f'{self.__class__.__name__}'
                f'{*self.possibilities, }')

    def strip(self, chars=" ", directions=[1, -1]):  # type: ignore[override]
        # type: (AnyStr, str, list[int]) -> AnyStr | str
        new = AnyStr(*self.possibilities)  # type: AnyStr | str
        for i in directions:
            if i == 1:
                sl = slice(1, len(self))  # type: ignore[misc]
                k = 0
            elif i == -1:
                sl = slice(0, -1)
                k = -1
            else:
                raise ValueError("each direction is expected to be 1 or -1, \
not {}".format(i))
            for char in chars:
                while new and new[k] == char:
                    new = new[sl]  # type: ignore[misc]
        return new

    def lstrip(self, chars=" "):  # type: ignore[override]
        # type: (AnyStr, str) -> AnyStr | str
        return self.strip(chars, directions=[1])

    def rstrip(self, chars=" "):  # type: ignore[override]
        # type: (AnyStr, str) -> AnyStr | str
        return self.strip(chars, directions=[-1])

    def isspace(self):
        # type: (AnyStr) -> bool
        for possibility in self.possibilities:
            if possibility.strip() == '':
                return True
        return False


class ManifoldStr(UserString):
    def __init__(self, data, rdict):
        # type: (ManifoldStr, str, dict[str, list[str]]) -> None
        """A string structure that takes an str `data' and a dictionary
 `rdict' where each key is a substring to be replaced, and
 corresponding value is an array of possible replacements of equal length. Each
 key in `replacement_dict' is replaced where found in `data' with an AnyStr
 containing key and replacements."""
        super().__init__(data)
        self.base = data
        self.rdict = rdict
        # A dictionary of strs and AnyStrs with the index of where each begins
        self.manifold = {0: data}  # type: Mapping[int, str | AnyStr]

        def makeCombined():
            # type: () -> str
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
        # type: (ManifoldStr, object) -> bool
        if s == self.data:
            return True
        elif isinstance(s, (str, UserString)):  # else check against substrings
            for i, substring in self.manifold.items():
                if s[i: i + len(substring)] != substring:
                    return False
            return True
        return False

    def _add(self, s, order=1):
        # type: (ManifoldStr, object, int) -> ManifoldStr
        args = None  # type: tuple[object, object] | None
        if order == 1:
            args = (self, s)
        elif order == -1:
            args = (s, self)
        else:
            raise ValueError("order is expected to be 1 or -1, not {}"
                             .format(order))

        if isinstance(s, str):
            return ManifoldStr.from_ms_and_str(self, s, order)
        if isinstance(s, AnyStr):
            return ManifoldStr.from_ms_and_anystr(self, s, order)
        if isinstance(s, ManifoldStr):
            return ManifoldStr.from_ms_and_ms(*args)
        else:
            raise TypeError('can only concatenate str, AnyStr, or ManifoldStr\
 (not "{}") to ManifoldStr'.format(type(s)))

    def __add__(self, s):
        # type: (ManifoldStr, object) -> ManifoldStr
        return self._add(s, 1)

    def __radd__(self, s):
        # type: (ManifoldStr, object) -> ManifoldStr
        return self._add(s, -1)

    def join(self, iterable):  # type: ignore[override]
        # type: (ManifoldStr, Iterable[str | UserString]) -> str | UserString
        result = ''  # type: str | UserString
        for s in iterable:
            if not result:
                result = s
            else:
                result += s
        return result

    def __getitem__(self, i):  # type: ignore[override]
        # type: (ManifoldStr, IndexOrSlice) -> UserString | str
        if isinstance(i, int):
            if i < 0:
                ni = len(self.data) + i
                if ni < 0:
                    raise IndexError('list index out of range')
                return self.__getitem__(ni)
            elif i in self.manifold:
                if len(self.manifold[i]) > 1:
                    return self.manifold[i][0]
                else:
                    return self.manifold[i]
            else:
                # Find substring before i, and extract just the index required
                descending_keys = sorted([*self.manifold], reverse=True)
                substring = k = None
                for k in descending_keys:
                    if k < i:
                        substring, k = (self.manifold[k], k)
                        break
                if substring is None or k is None:
                    raise KeyError
                return substring[i - k]
        elif isinstance(i, slice):  # type: ignore[misc]
            start, stop, step = i.indices(len(self))
            if step == 1:
                descending_keys = sorted([*self.manifold], reverse=True)
                substring_by_start = substring_by_stop = None
                new_manifold = {}
                for k in descending_keys:
                    index = 0 if k == 0 else k-start
                    if start <= k < stop:
                        new_manifold[index] = self.manifold[k]
                    if not substring_by_stop:
                        if k < stop:
                            substring_by_stop = self.manifold[k]
                            new_manifold[index] = substring_by_stop[:stop-k]
                    if k < start:
                        substring_by_start = self.manifold[k]
                        s = substring_by_start[start-k:]
                        if len(s):
                            new_manifold[index] = s
                        break
                return ManifoldStr.by_parts(self.data[start:stop],
                                            self.rdict,
                                            new_manifold)
            else:
                return self.join([self[j] for j in range(start, stop, step)])
        else:
            raise TypeError("ManifoldStr indices must be integers or slices,\
 not {}".format(type(i)))

    def __repr__(self):
        # type: (ManifoldStr) -> str
        return (f'{self.__class__.__name__}'
                f'({repr(self.base)}, {self.rdict})')

    def strip(self, chars=" ", directions=[1, -1]):  # type: ignore[override]
        # type: (ManifoldStr, str, list[int]) -> UserString | str
        new = deepcopy(self)  # type: UserString | str
        for i in directions:
            if i == 1:
                sl = slice(1, len(self))  # type: ignore[misc]
                k = 0
            elif i == -1:
                sl = slice(0, -1)
                k = -1
            else:
                raise ValueError("each direction is expected to be 1 or -1, \
not {}".format(i))
            for char in chars:
                while new and new[k] == char:
                    new = new[sl]  # type: ignore[misc]
        return new

    def lstrip(self, chars=" "):  # type: ignore[override]
        # type: (ManifoldStr, str) -> UserString | str
        return self.strip(chars, directions=[1])

    def rstrip(self, chars=" "):  # type: ignore[override]
        # type: (ManifoldStr, str) -> UserString | str
        return self.strip(chars, directions=[-1])

    def isspace(self):
        # type: (ManifoldStr) -> bool
        if self.strip() == '':
            return True
        return False

    @classmethod
    def by_parts(cls,  # type: type[ManifoldStr]
                 data,  # type: str
                 rdict,  # type: dict[str, list[str]]
                 manifold  # type: Mapping[int, str | AnyStr]
                 ):
        # type: (...) -> ManifoldStr
        new = cls.__new__(cls)
        super().__init__(new, data)
        new.base = data
        new.rdict = rdict
        new.manifold = manifold
        return new

    @classmethod
    def from_anystr_and_anystr(cls, anystr1, anystr2):
        # type: (type[ManifoldStr], AnyStr, AnyStr) -> ManifoldStr
        data = anystr1.base + anystr2.base
        rdict = {anystr1.base: anystr1.possibilities[1:],
                 anystr2.base: anystr2.possibilities[1:]}
        manifold = {0: anystr1, len(anystr1): anystr2}
        new = cls.by_parts(data, rdict, manifold)
        logger.debug("New ManifoldStr from AnyStr '{}' and AnyStr '{}':\
 '{}'".format(anystr1, anystr2, new))
        return new

    @classmethod
    def from_str_and_anystr(cls, str_, anystr, order=1):
        # type: (type[ManifoldStr], str, AnyStr, int) -> ManifoldStr
        data = None
        manifold = None  # type: Mapping[int, str | AnyStr] | None
        if order == 1:
            data = str_ + anystr.base
            manifold = {0: str_, len(str_): anystr}
        elif order == -1:
            data = anystr.base + str_
            manifold = {0: anystr, len(anystr): str_}
        else:
            raise ValueError("order is expected to be 1 or -1, not {}"
                             .format(order))

        rdict = {anystr.base: anystr.possibilities[1:]}

        new = cls.by_parts(data, rdict, manifold)
        logger.debug(f"New ManifoldStr from str '{str_}' and AnyStr '{anystr}'"
                     f" (order {order}): '{new}'")
        return new

    @classmethod
    def from_anystr_and_str(cls, anystr, str_):
        # type: (type[ManifoldStr], AnyStr, str) -> ManifoldStr
        return cls.from_str_and_anystr(str_, anystr, -1)

    @classmethod
    def from_ms_and_anystr(cls, ms, anystr, order=1):
        # type: (type[ManifoldStr], ManifoldStr, AnyStr, int) -> ManifoldStr
        data = manifold = None
        if order == 1:
            data = ms.base + anystr.base
            manifold = {**ms.manifold, len(ms): anystr}
        elif order == -1:
            data = anystr.base + ms.base
            manifold = {0: anystr}
            for key, value in ms.manifold.items():
                manifold[key + len(anystr)] = value
        else:
            raise ValueError("order is expected to be 1 or -1, not {}"
                             .format(order))

        rdict = {**deepcopy(ms.rdict), anystr.base: anystr.possibilities[1:]}

        new = cls.by_parts(data, rdict, manifold)
        logger.debug("New ManifoldStr from ManifoldStr '{}' and AnyStr '{}':\
 '{}'".format(ms, anystr, new))
        return new

    @classmethod
    def from_anystr_and_ms(cls, anystr, ms):
        # type: (type[ManifoldStr], AnyStr, ManifoldStr) -> ManifoldStr
        return cls.from_ms_and_anystr(ms, anystr, -1)

    @classmethod
    def from_ms_and_str(cls, ms, str_, order=1):
        # type: (type[ManifoldStr], ManifoldStr, str, int) -> ManifoldStr
        rdict = deepcopy(ms.rdict)
        if order == 1:
            return ms + ManifoldStr(str_, rdict)
        elif order == -1:
            return ManifoldStr(str_, rdict) + ms
        else:
            raise ValueError("order is expected to be 1 or -1, not {}"
                             .format(order))

    @classmethod
    def from_str_and_ms(cls, str_, ms):
        # type: (type[ManifoldStr], str, ManifoldStr) -> ManifoldStr
        return cls.from_ms_and_str(ms, str_, -1)

    @classmethod
    def from_ms_and_ms(cls, ms1, ms2):
        # type: (type[ManifoldStr], ManifoldStr, ManifoldStr) -> ManifoldStr
        data = ms1.base + ms2.base
        rdict = deepcopy(ms1.rdict)
        for k, v in ms2.rdict.items():
            rdict[k] = v
        return ManifoldStr(data, rdict)


if TYPE_CHECKING:
    from typing import (  # noqa: F401
        Iterable, SupportsIndex, Mapping)
    IndexOrSlice = SupportsIndex | slice
