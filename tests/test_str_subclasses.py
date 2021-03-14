import logging
from retype.extras import AnyStr, ManifoldStr
from retype.console.highlighting_service import compareStrings


logger = logging.getLogger('str_subclasses')
logger.setLevel(logging.DEBUG)


class TestAnyStr:
    def test_construction(self):
        s = AnyStr('1', '2', '3', '4', '5')
        assert s.possibilities == ('1', '2', '3', '4', '5')

    def test_eq(self):
        s = AnyStr('1', '2', '3', '4', '5')
        for p in s.possibilities:
            assert s == p

    def test_add_str(self):
        s = AnyStr('1', '2')
        new = s + " more"
        assert new.possibilities == ('1 more', '2 more')

        # But if you add in the opposite order it doesn’t work, because our
        #  method doesn’t even get called

    def test_add_anystr(self):
        s = AnyStr('1', '2')
        s2 = AnyStr('3', '4')
        new = s + s2
        assert new.possibilities == ('13', '24')

    def test_getitem_int(self):
        s = AnyStr('some', 'poss', 'reps')
        for p in s.possibilities:
            assert s[0] == p[0]
            assert s[2] == p[2]
            assert s[-1] == p[-1]

    def test_getitem_slice(self):
        s = AnyStr('some', 'poss', 'reps')
        assert s[:3].possibilities == ('som', 'pos', 'rep')

    def test_getitem_slice_negative(self):
        s = AnyStr('some', 'poss', 'reps')
        assert s[:-1].possibilities == ('som', 'pos', 'rep')

    def test_rstrip(self):
        s = AnyStr('1   ', '2   ')
        new = s.rstrip()
        assert new.possibilities == ('1', '2')
        # Assert original has not been mutated
        assert s.possibilities == ('1   ', '2   ')


def getMS(string, replacements_dict):
    ms = ManifoldStr(string, replacements_dict)
    anystrs = {k: AnyStr(k, *v) for k, v in replacements_dict.items()}
    return ms, anystrs


def assertProperMSConstruction(ms, expected_manifold):
    assert ms.manifold == expected_manifold


class TestManifoldStr:
    def test_construction_one_replacement(self):
        ms, anystrs = getMS("some text", {'s': ['o']})
        expected_manifold = {0: anystrs['s'], 1: 'ome text'}
        assertProperMSConstruction(ms, expected_manifold)

    def test_construction_replacement_that_appears_twice(self):
        ms, anystrs = getMS("some text", {'t': ['o']})
        expected_manifold = {0: 'some ', 5: anystrs['t'], 6: 'ex',
                             8: anystrs['t']}
        assertProperMSConstruction(ms, expected_manifold)

    def test_construction_threeletter_replacement(self):
        ms, anystrs = getMS("some text", {'tex': ['yoo', 'nop']})
        expected_manifold = {0: 'some ', 5: anystrs['tex'], 8: 't'}
        assertProperMSConstruction(ms, expected_manifold)

    def test_construction_multiple_replacements(self):
        ms, anystrs = getMS("some text with multiple replacements",
                            {'tex': ['yoo', 'nop'],
                             'rep': ['ded', 'led', 'red']})
        expected_manifold = {
            0: 'some ', 5: anystrs['tex'], 8: 't with multiple ',
            24: anystrs['rep'], 27: 'lacements'
        }
        assertProperMSConstruction(ms, expected_manifold)

    def test_construction_multiple_replacements_opposite_order(self):
        ms, anystrs = getMS("some text with multiple replacements",
                            {'rep': ['ded', 'led', 'red'],
                             'tex': ['yoo', 'nop']})
        expected_manifold = {
            0: 'some ', 5: anystrs['tex'], 8: 't with multiple ',
            24: anystrs['rep'], 27: 'lacements'
        }
        assertProperMSConstruction(ms, expected_manifold)

    def test_construction_with_only_one_character(self):
        ms, anystrs = getMS("a", {'a': ['b', 'c']})
        expected_manifold = {0: anystrs['a']}
        assertProperMSConstruction(ms, expected_manifold)

    def test_eq(self):
        string = "thou art an eternal babbler; and, though void of wit,\
 your bluntness often occasions smarting"
        ms = ManifoldStr(string, {'babbler': ['cackler', 'rattler'],
                                  'wit': ['cat'],
                                  'blunt': ['smart', 'stump']})
        assert ms == string
        assert ms == "thou art an eternal babbler; and, though void of cat,\
 your smartness often occasions smarting"
        assert ms != "thou art an ofiejwofjiweopfawiehfaowiehfao"
        assert ms != "thou art an eternal babbler; and, though void of cat,\
 your smartness often accasions smarting"

    def test_add_str(self):
        ms = ManifoldStr("hello", {"e": "a"})
        result = ms + " friend"
        assert result == "hello friend"
        assert result == "hallo friend"
        assert result == "hallo friand"

    def test_add_anystr(self):
        ms = ManifoldStr("hello", {"e": "a"})
        anystr = AnyStr(" friend", " birdie")
        assert ms + anystr == "hallo friend"
        # assert ms + anystr == "hallo birdie"
        # doesn’t work because the e -> a replacement is already made so it
        #  doesn’t find friend

    def test_add_manifoldstr(self):
        ms = ManifoldStr("hello", {"e": "a"})
        ms2 = ManifoldStr(" people", {"o": "i"})
        assert ms + ms2 == "halli paopla"

    def test_getitem(self):
        ms = ManifoldStr("some text", {'t': ['a', 'b'], 's': ['d']})
        assert type(ms[0]) is AnyStr
        assert ms[0] == 's'
        assert ms[0] == 'd'
        assert ms[1] == 'o'
        assert ms[1] != 'a'
        assert ms[-1] == 'b'

    def test_getitem_slice(self):
        ms = ManifoldStr("some text", {'t': ['a', 'b'], 's': ['d']})
        assert ms[:4] == "dome"

    def test_with_compareStrings(self):
        string = "thou art an eternal babbler; and, though void of wit,\
 your bluntness often occasions smarting"
        ms = ManifoldStr(string, {'babbler': ['cackler', 'rattler'],
                                  'wit': ['cat'],
                                  'blunt': ['smart', 'stump']})

        input_ = "thou art an eternal cackler; and, though void of cat"
        end_correctness_index = compareStrings(input_, ms)
        assert end_correctness_index == len(input_)

    def test_rstrip(self):
        ms = ManifoldStr("hey  ", {'hey': ['bye']})
        assert ms.rstrip() == "hey"
        assert ms.rstrip() == "bye"

    def test_rstrip_nothing_to_strip(self):
        ms = ManifoldStr("a", {'a': ['b']})
        assert ms.rstrip() == "b"

    def test_rstrip_only_one_character(self):
        ms = ManifoldStr("a", {'a': [' ']})
        assert ms.rstrip() == ""

    def test_rstrip_unicode(self):
        ms = ManifoldStr("\ufffc", {'\ufffc': [' ']})
        assert ms.rstrip() == ""

    def test_strip_only_one_character(self):
        ms = ManifoldStr("a", {'a': [' ']})
        assert ms.strip() == ""

    def test_isspace(self):
        ms = ManifoldStr("a", {'a': [' ']})
        assert ms.isspace() is True

    def test_isspace_not_space(self):
        ms = ManifoldStr("hey  ", {'hey': ['bye']})
        assert ms.isspace() is False

    def test_discworld(self):
        ms = ManifoldStr("A Discworld® Novel", {"®": {'r', 'R'}})
        assert ms == "A Discworldr Novel"
