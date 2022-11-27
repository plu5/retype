import re
from setuptools import setup
from setup.build import b


pkg_file = open("retype/__init__.py").read()
metadata = dict(re.findall(r"__([a-z]+)__\s*=\s*'([^']+)'", pkg_file))


setup(name='retype',
      version=metadata['version'],
      packages=['qt', 'retype'],
      zip_safe=False,
      install_requires=[
          'PyQt5',
          'ebooklib',
      ],
      cmdclass={
          'b': b,  # custom build command for building retype with pyinstaller
      },)
