Build instructions
==================

#. Get a local copy of `the code repository <https://github.com/plu5/retype>`_: either clone it or download and extract `ZIP of latest <https://github.com/plu5/retype/archive/main.zip>`_   
#. Install the :doc:`dependencies <dependencies>`
#. Install ``pyinstaller`` and ``setuptools``
#. Run ``python setup.py b`` and help text will print with the build options you can use. For example, ``python setup.py b -k onedir`` will build retype with pyinstaller in onedir mode.

The output will be in ``/dist``.
