from os.path import join
from setup.config import util


class TestUtil:
    def test_getroot(self):
        dest = join('lxml', 'isoschematron', 'resources' 'xsl')
        assert util.getRoot(dest) == 'lxml'
