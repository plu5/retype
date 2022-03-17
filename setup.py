from setuptools import setup
from setup.build import b


setup(name='retype',
      version='1.0.0',
      packages=['qt', 'retype'],
      zip_safe=False,
      install_requires=[
          'PyQt5',
          'ebooklib',
      ],
      cmdclass={
          'b': b,  # custom build command for building retype with pyinstaller
      },)
