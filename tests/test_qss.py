from tinycss2 import parse_stylesheet, parse_declaration_list

from retype.extras.qss import (findSelector, getCValue, serialiseProp,
                               serialiseValuesDict)


def parseS(x):
    return parse_stylesheet(x, True, True)


def parseD(x):
    return parse_declaration_list(x, True, True)


class TestQssFindSelector:
    def test_oneword_selector_that_exists(self):
        res = findSelector('oneword', parseS('oneword {}'))
        assert res == []

    def test_oneword_selector_that_does_not_exist(self):
        res = findSelector('oneword', parseS('differentword {}'))
        assert res is None

    def test_selector_with_dot_that_exists(self):
        res = findSelector('selector.withdot', parseS('selector.withdot {}'))
        assert res == []

    def test_selector_with_dot_different_after_dot(self):
        res = findSelector('selector.withdot', parseS('selector.different {}'))
        assert res is None

    def test_selector_with_dot_whitespace_after_dot(self):
        res = findSelector('selector.withdot', parseS('selector. withdot {}'))
        assert res is None

    def test_correct_selector_with_whitespace(self):
        res = findSelector('selector', parseS('  selector   {}'))
        assert res == []

    def test_incorrect_selector_with_whitespace(self):
        res = findSelector('selector', parseS('  selector  .f  {}'))
        assert res is None

    def test_complex_selector(self):
        res = findSelector('*[accessibleName="console"]',
                           parseS('*[accessibleName="console"] {}'))
        assert res == []


class TestQssGetCValue():
    def test_existing_identifier_no_whitespace(self):
        res = getCValue('color', parseD('color:qwer;'))
        assert res == 'qwer'

    def test_existing_identifier_hash(self):
        res = getCValue('color', parseD('color: #qwer;'))
        assert res == '#qwer'

    def test_existing_hyphenated_identifier(self):
        res = getCValue('background-color',
                        parseD('background-color: #qwer;'))
        assert res == '#qwer'

    def test_nonexisting_hyphenated_identifier(self):
        res = getCValue('color',
                        parseD('background-color: #qwer;'))
        assert res is None

    def test_argb_cvalue(self):
        res = getCValue('color',
                        parseD('color: #80ffff00;'))
        assert res == '#80ffff00'


class TestSerialiseProp():
    def test_prop(self):
        res = serialiseProp('test', 'val')
        assert res == 'test: val;'


class TestSerialiseValuesDict():
    def test_one_selector_one_prop(self):
        d = {'selector1': {'prop1': 'value1'}}
        res = serialiseValuesDict(d)
        assert res == 'selector1 {\n  prop1: value1;\n}\n\n'

    def test_two_selectors(self):
        d = {'selector1': {'prop1': 'value1'},
             'selector2': {'a': 'v1', 'b': 'v2'}}
        res = serialiseValuesDict(d)
        assert res == 'selector1 {\n  prop1: value1;\n}\n\n\
selector2 {\n  a: v1;\n  b: v2;\n}\n\n'
