import os
import re


def getVersionStr(path):
    pkg_file = open(os.path.join(path, "retype/__init__.py")).read()
    metadata = dict(re.findall(r"__([a-z]+)__\s*=\s*'([^']+)'", pkg_file))
    return metadata['version']
