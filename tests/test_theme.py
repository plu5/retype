from retype.services.theme import valuesFromQss


class TestThemeValuesFromQss:
    def test_one_value(self):
        qss = """ShelfView.Top {border-top-color: #A1A0A0;
 border-bottom-color: #555;}"""
        d = {'ShelfView.Top': {'border-top-color': None}}
        res = valuesFromQss(d, qss)
        assert res == {'ShelfView.Top': {'border-top-color': '#A1A0A0'}}

    def test_both_values(self):
        qss = """ShelfView.Top {border-top-color: #A1A0A0;
 border-bottom-color: #555;}"""
        d = {'ShelfView.Top': {'border-top-color': None,
                               'border-bottom-color': None}}
        res = valuesFromQss(d, qss)
        assert res == {'ShelfView.Top': {'border-top-color': '#A1A0A0',
                                         'border-bottom-color': '#555'}}

    def test_nonexisting_selector(self):
        qss = ""
        d = {'ShelfView.Top': {'border-top-color': None}}
        res = valuesFromQss(d, qss)
        assert res == {}

    def test_complex_selector(self):
        qss = """*[accessibleName="console"] {border-top-color: #A1A0A0;
 border-bottom-color: #555;}"""
        d = {'*[accessibleName="console"]': {'border-bottom-color': None}}
        res = valuesFromQss(d, qss)
        assert res == {'*[accessibleName="console"]':
                       {'border-bottom-color': '#555'}}

    def test_one_existing_one_nonexisting_selector(self):
        qss = "test{t:red;}"
        d = {'ShelfView.Top': {'border-top-color': None}, 'test': {'t': None}}
        res = valuesFromQss(d, qss)
        assert res == {'test': {'t': 'red'}}

    def test_one_existing_one_nonexisting_prop(self):
        qss = "test{t:red;}"
        d = {'test': {'t': None, 'color': None}}
        res = valuesFromQss(d, qss)
        assert res == {'test': {'t': 'red'}}

    def test_one_existing_one_nonexisting_selector_and_prop(self):
        qss = "test{t:red;}"
        d = {'ShelfView.Top': {'border-top-color': None, 't': None},
             'test': {'t': None, 'color': None}}
        res = valuesFromQss(d, qss)
        assert res == {'test': {'t': 'red'}}
