from setup.config import util


class TestUtil:
    def test_getroot(self):
        dest = "lxml\\isoschematron\\resources\\xsl"
        assert util.getRoot(dest) == 'lxml'
