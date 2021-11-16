import logging
from retype.extras import AnyStr, ManifoldStr
from retype.console.highlighting_service import compareStrings


logger = logging.getLogger('str_subclasses')
logger.setLevel(logging.DEBUG)


class TestAnyStr:
    def test_construction(self):
        s = AnyStr('1', '2', '3', '4', '5')
        assert s.possibilities == ['1', '2', '3', '4', '5']

    def test_eq(self):
        s = AnyStr('1', '2', '3', '4', '5')
        for p in s.possibilities:
            assert s == p

    def test_add_str_to_anystr(self):
        s = AnyStr('1', '2')
        new = s + " more"
        assert new == "1 more"
        assert new == "2 more"

    def test_add_anystr_to_str(self):
        s = AnyStr('1', '2')
        new = "additional " + s
        assert new == "additional 1"
        assert new == "additional 2"

    def test_add_anystr_to_anystr(self):
        s = AnyStr('1', '2')
        s2 = AnyStr('3', '4')
        new = s + s2
        assert new == "13"
        assert new == "24"
        assert new == "14"
        assert new == "23"

    def test_getitem_full(self):
        s = AnyStr('some', 'poss', 'reps')
        assert s[0:4] == 'some'
        assert s[0:4] == 'poss'

    def test_getitem_int(self):
        s = AnyStr('some', 'poss', 'reps')
        assert s[0] == s.possibilities[0][0]
        assert s[0] != s.possibilities[0][1]

    def test_getitem_slice(self):
        s = AnyStr('some', 'poss', 'reps')
        assert s[0:3] == 'som'
        assert s[0:3] != 'pos'

    def test_getitem_slice_negative(self):
        s = AnyStr('some', 'poss', 'reps')
        assert s[:-1] == 'som'
        assert s[:-1] != 'rep'

    def test_rstrip(self):
        s = AnyStr('1   ', '2   ')
        new = s.rstrip()
        assert new == '1'
        assert new != '2'
        # Assert original has not been mutated
        assert s.possibilities == ['1   ', '2   ']

    def test_isspace_first_possibility(self):
        s = AnyStr("      ", "anystr")
        assert s.isspace() is True

    def test_isspace_second_possibility(self):
        s = AnyStr("anystr", "      ")
        assert s.isspace() is True

    def test_isspace_not_space(self):
        s = AnyStr("      1.1 Algorithms", "      1.2 Algorithms")
        assert s.isspace() is False


def getMS(string, rdict):
    ms = ManifoldStr(string, rdict)
    anystrs = {k: AnyStr(k, *v) for k, v in rdict.items()}
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

    def test_add_str_to_manifoldstr(self):
        ms, anystrs = getMS("hello", {"e": "a"})
        result = ms + " friend"
        assert result == "hello friend"
        assert result == "hallo friend"
        assert result == "hallo friand"

        # Assert original has not been mutated
        assert ms == "hello"
        assert ms == "hallo"
        assert ms.manifold == {0: 'h', 1: anystrs['e'], 2: 'llo'}

    def test_add_manifoldstr_to_str(self):
        ms, anystrs = getMS("hello", {"e": "a"})
        result = "hi and " + ms
        assert result == "hi and hallo"

        # Assert original has not been mutated
        assert ms == "hallo"
        assert ms.manifold == {0: 'h', 1: anystrs['e'], 2: 'llo'}

    def test_add_anystr_to_manifoldstr(self):
        ms = ManifoldStr("hello", {"e": "a"})
        anystr = AnyStr(" friend", " birdie")
        assert ms + anystr == "hallo friend"
        # assert ms + anystr == "hallo birdie"
        # doesn’t work because the e -> a replacement is already made so it
        #  doesn’t find friend

    def test_add_manifoldstr_to_anystr(self):
        anystr = AnyStr("hi and ", "yo and ")
        ms = ManifoldStr("hello", {"e": "a"})
        assert anystr + ms == "yo and hallo"

    def test_add_manifoldstr_to_manifoldstr(self):
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

    def test_getitem_negative_slice(self):
        ms = ManifoldStr("some text", {'t': ['a', 'b'], 's': ['d']})
        assert ms[:-1] == "dome tex"
        assert ms[-4:-1] == "bex"

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

    def test_rstrip_multiple_replacements(self):
        ms, anystrs = getMS("some text with multiple replacements  ",
                            {'tex': ['yoo', 'nop'],
                             'rep': ['ded', 'led', 'red']})
        assert ms.rstrip() == "some yoot with multiple replacements"

    def test_isspace(self):
        ms = ManifoldStr("a", {'a': [' ']})
        assert ms.isspace() is True

    def test_isspace_not_space(self):
        ms = ManifoldStr("hey  ", {'hey': ['bye']})
        assert ms.isspace() is False

    def test_isspace_not_space2(self):
        ms = ManifoldStr("      1.1 Algorithms", {'\ufffc': ' '})
        assert ms.isspace() is False

    def test_discworld(self):
        ms = ManifoldStr("A Discworld® Novel", {"®": {'r', 'R'}})
        assert ms == "A Discworldr Novel"
