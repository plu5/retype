from tinycss2.serializer import serialize
from tinycss2.ast import (QualifiedRule, Declaration, IdentToken, LiteralToken,
                          WhitespaceToken, HashToken)

from typing import TYPE_CHECKING


def findSelector(selector, input_):
    # type: (str, Iterable[Node]) -> Iterable[Node] | None
    """Find selector in input, where input the output of tinycss2 parsing.
Return content of rule matching selector if found, None if not found."""
    content = None
    for item in input_:
        if isinstance(item, QualifiedRule):
            prelude = item.prelude
            current_selector = serialize(prelude)
            if current_selector.strip().lower() == selector.lower():
                content = item.content
                break
    return content


def getCValue(identifier, declarations):
    # type: (str, Iterable[Node]) -> str | None
    """Find colour value of identifier in tinycss2 declaration list.
Return colour value of identifier if found, None if not found."""
    value = None
    for item in declarations:
        if isinstance(item, Declaration) and item.lower_name == identifier:
            value_list = item.value
            filtered = []
            for token in value_list:
                if isinstance(token, (IdentToken, LiteralToken,
                                      WhitespaceToken)):
                    filtered.append(token.value)
                elif isinstance(token, HashToken):
                    filtered.append('#')
                    filtered.append(token.value)
            value = ''.join(filtered).strip()
            break
    return value


INDENTATION = '  '


def serialiseProp(prop_name, value):
    # type: (str, str) -> str
    return f'{prop_name}: {value};'


def serialiseValuesDict(values):
    # type: (dict[str, dict[str, str]]) -> str
    res = []  # type: list[str]
    for selector_name, props in values.items():
        res.append(str(selector_name))
        res.append(' {\n')
        for prop_name, value in props.items():
            res.append(INDENTATION)
            res.append(serialiseProp(prop_name, value))
            res.append('\n')
        res.append('}\n\n')
    return ''.join(res)


if TYPE_CHECKING:
    from typing import Iterable  # noqa: F401
    from tinycss2.ast import Node  # noqa: F401
