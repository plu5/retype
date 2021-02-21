import os
import sys

try:
    __file__
except NameError:
    __file__ = sys.argv[0]

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from retype import app  # noqa: E402
app.run()
