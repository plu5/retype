from tinycss2 import serialize


def findSelector(selector, input_):
    """Find selector in input, where input the output of tinycss2 parsing.
Return content of rule matching selector if found, None if not found."""
    content = None
    for item in input_:
        if item.type != 'qualified-rule':
            continue
        prelude = item.prelude
        current_selector = serialize(prelude)
        if current_selector.strip().lower() == selector.lower():
            content = item.content
            break
    return content


def getCValue(identifier, declarations):
    """Find colour value of identifier in tinycss2 declaration list.
Return colour value of identifier if found, None if not found."""
    value = None
    for item in declarations:
        if item.type == 'declaration' and item.lower_name == identifier:
            value_list = item.value
            current_value = ''
            for token in value_list:
                if token.type in ['ident', 'literal', 'whitespace']:
                    current_value += token.value
                elif token.type == 'hash':
                    current_value += '#' + token.value
            value = current_value.strip()
            break
    return value


INDENTATION = '  '


def serialiseProp(prop_name, value):
    return f'{prop_name}: {value};'


def serialiseValuesDict(values):
    res = ''
    for selector_name, props in values.items():
        res += selector_name + ' {\n'
        for prop_name, value in props.items():
            res += INDENTATION + serialiseProp(prop_name, value) + '\n'
        res += '}\n\n'
    return res
