from retype.extras.split import splittext


sdict = {
    '\r\n': {'keep': False},
    '\n': {'keep': False},
    '. ': {'keep': True}
}


class TestSplitText:
    def test_lf(self):
        res = splittext("hello\nthere\nworld", sdict)
        assert res == ["hello", "there", "world"]

    def test_crlf(self):
        res = splittext("hello\r\nthere\r\nworld", sdict)
        assert res == ["hello", "there", "world"]

    def test_crlf_and_periodspace(self):
        res = splittext("hello\r\nthere\r\nworld. how", sdict)
        assert res == ["hello", "there", "world. ", "how"]

    def test_indicatenewlines(self):
        res = splittext("Flatland \nEdwin A. Abbott ", sdict,
                        indicatenewlines=True)
        assert res == ["Flatland \n", "Edwin A. ", "Abbott "]

    def test_keeplength(self):
        res = splittext("Flat..land..Edwin", {'..': {'keep': False}},
                        fill=" ")
        assert res == ["Flat  ", "land  ", "Edwin"]
