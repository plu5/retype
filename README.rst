.. raw:: html

  <h1>
  <img src="https://raw.githubusercontent.com/plu5/retype/main/docs/_static/img/retype.ico" width="32"/>
  retype
  </h1>

|version-badge| |docs-badge|
  
*retype* is a free and open-source typing practice application that allows you to type along to epub books. It saves your progress so you can come back where you left off.

.. figure:: https://raw.githubusercontent.com/plu5/retype/main/docs/_static/img/col.png
   :align: center

|
:Source code:   https://github.com/plu5/retype
:Issue tracker: https://github.com/plu5/retype/issues
:Documentation: https://retype.readthedocs.io/

.. _documentation: https://retype.readthedocs.io/

.. contents::

-----
Usage
-----

To run retype, you can `download the latest build for your operating system <https://github.com/plu5/retype/releases/latest>`_, `build it yourself <#build-instructions>`_, or `run it from sources <#running-from-sources>`_.

Build instructions
^^^^^^^^^^^^^^^^^^

#. Get a local copy of this repository: either clone it or download and extract `ZIP of latest <https://github.com/plu5/retype/archive/main.zip>`_   
#. Install the `dependencies`_ [``pip3 install -r requirements.txt``]
#. Install ``pyinstaller`` and ``setuptools`` [``pip3 install pyinstaller setuptools``]
#. Run ``python3 setup.py b`` and help text will print with the build options you can use. For example, ``python3 setup.py b -k onedir`` will build retype with pyinstaller in onedir mode.

The output will be in ``/dist``.

Running from sources
^^^^^^^^^^^^^^^^^^^^

#. Get a local copy of this repository: either clone it or download and extract `ZIP of latest <https://github.com/plu5/retype/archive/main.zip>`_   
#. Install the `dependencies`_ [``pip3 install -r requirements.txt``]
#. Run ``bin/retype``. On Windows, you can simply double-click on ``bin/retype.pyw``. From console, you can run ``python3 bin/retype``.

Dependencies
^^^^^^^^^^^^

**Required:**

- Python 3.7 or higher
- ``PyQt5``
- ``ebooklib``
- ``tinycss2``

**Optional:**

- ``pywin32`` -- Windows-only. This is only used for optionally hiding the System Console window.
- ``pytest`` -- to run tests
- ``pyinstaller`` and ``setuptools`` -- to build retype
- ``Sphinx`` and ``sphinx-rtd-theme`` -- to build the docs locally
  
Getting started
^^^^^^^^^^^^^^^
 
When you launch retype, you should see 5 epub books that it comes with of short classic works. You can begin reading one of them by clicking on its cover or entering ``>load #`` into the console, where ``#`` is the numerical id of the book which can be seen above the cover.

Type to progress through the book. You can see your current speed in words per minute on the graph above the modeline and your personal best.

Other than typing, you can navigate the book with toolbar buttons and console commands.

You can add more library search paths and customise retype’s operation in the Customisation Dialog, which can be accessed from the menu or by :kbd:`Ctrl+O`.

More information on the user interface and available features can be found in the documentation_.

-----------------------------
Influences & acknowledgements
-----------------------------

- `QTodoTxt <https://github.com/QTodoTxt/QTodoTxt>`_
- `calibre 3 <https://github.com/kovidgoyal/calibre/tree/v3.48.0>`_
- `Blender <https://github.com/blender/blender>`_
- `Standard Ebooks <https://github.com/standardebooks/>`_
- `Typespeed <https://typespeed.sourceforge.net/>`_
- `Steno Jig <https://github.com/joshuagrams/steno-jig>`_


.. |version-badge| image:: https://img.shields.io/github/v/release/plu5/retype?color=success&label=stable
   :alt: GitHub latest release
   :target: ../../releases/latest
.. |docs-badge| image:: https://img.shields.io/readthedocs/retype
   :alt: Read the Docs
   :target: https://retype.readthedocs.io/
