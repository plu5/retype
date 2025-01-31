from collections.abc import Mapping
from copy import deepcopy
from functools import reduce

from typing import TYPE_CHECKING


# RubyPinch https://www.reddit.com/r/Python/comments/477tqv/-/d0c1dz5/
def merge_dicts(*dicts):
    # type: (Mapping) -> Any
    """Merge nested dicts as copy"""
    return deepcopy(reduce(
        lambda a, b: {**a, **b}, dicts))  # type: ignore[misc]


def update(source, overrides):
    # type: (dict, Mapping) -> dict
    # by charlax, https://stackoverflow.com/a/30655448
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.
    """
    for key, value in overrides.items():          # type: ignore[misc]  # (Any)
        if isinstance(value, Mapping) and value:  # type: ignore[misc]
            returned = update(                    # type: ignore[misc]
                source.get(key, {}), value)       # type: ignore[misc]
            source[key] = returned                # type: ignore[misc]
        else:
            source[key] = overrides[key]          # type: ignore[misc]
    return source                                 # type: ignore[misc]


class SafeDict:
    def __init__(self,  # type: SafeDict
                 base_dict,  # type: Mapping
                 fallback_dict=None,  # type: Mapping | None
                 nested_raw_dict_keys=None  # type: Sequence[object] | None
                 ):
        # type: (...) -> None
        self.raw = base_dict  # type: NestedDict  # type: ignore[assignment]
        fallback = fallback_dict  # type: NestedMapping | None
        self.fallback = fallback or {}
        self.nested_raw_dict_keys = nested_raw_dict_keys or []

    def __getitem__(self,  # type: SafeDict
                    key,  # type: object
                    default=None  # type: object | None
                    ):
        # type: (...) -> Union[object, _NestedSafeDictGroup]
        r = self.raw.get(key, self.fallback.get(key, default))
        if isinstance(r, dict) and key not in self.nested_raw_dict_keys:
            return _NestedSafeDictGroup(key, r, self.fallback)
        return r

    def __setitem__(self, key, value):
        # type: (SafeDict, object, Union[object, NestedDict]) -> None
        if isinstance(value, dict) and key not in self.nested_raw_dict_keys:
            self.raw.setdefault(key, _NestedSafeDictGroup(
                key, value, self.fallback))
        else:
            self.raw[key] = value

    def get(self,  # type: SafeDict
            key,  # type: object
            default=None  # type: object | None
            ):
        # type: (...) -> Union[object, _NestedSafeDictGroup]
        return self.__getitem__(key, default)

    def update(self, overrides):
        # type: (SafeDict, Mapping) -> None
        self.raw = update(self.raw, overrides)  # type: ignore[misc]

    def deepcopy(self):
        # type: () -> SafeDict
        raw_copy = deepcopy(self.raw)  # type: NestedDict
        return SafeDict(raw_copy, self.fallback, self.nested_raw_dict_keys)

    def values(self):
        # type: () -> ValuesView
        return self.raw.values()

    def items(self):
        # type: () -> ItemsView
        return self.raw.items()


class _NestedSafeDictGroup:
    def __init__(self,  # type: _NestedSafeDictGroup
                 name,  # type: object
                 group,  # type: dict
                 fallback_dict=None  # type: Mapping | None
                 ):
        # type: (...) -> None
        self.name = name
        self.raw = self.group = group  # type: NestedDict
        fallback = fallback_dict  # type: NestedMapping | None
        self.fallback = fallback or {}

    def __getitem__(self, key, default=None):
        # type: (_NestedSafeDictGroup, object, object | None) -> object
        if key in self.group:
            return self.group[key]
        d = self.fallback.get(self.name)
        return d.get(key, default) if isinstance(d, Mapping) else default

    def __setitem__(self, key, value):
        # type: (_NestedSafeDictGroup, object, NestedDict) -> None
        self.raw[key] = value

    def get(self, key, default=None):
        # type: (_NestedSafeDictGroup, object, object | None) -> object
        return self.__getitem__(key, default)

    def update(self, overrides):
        # type: (_NestedSafeDictGroup, Mapping) -> None
        self.raw = update(self.raw, overrides)  # type: ignore[misc]

    def values(self):
        # type: (_NestedSafeDictGroup) -> ValuesView
        return self.raw.values()

    def items(self):
        # type: (_NestedSafeDictGroup) -> ItemsView
        return self.raw.items()


if TYPE_CHECKING:
    from typing import (  # noqa: F401
        Union, Dict, ValuesView, ItemsView, Sequence, Any)
    from retype.extras.metatypes import NestedDict, NestedMapping  # noqa: F401
