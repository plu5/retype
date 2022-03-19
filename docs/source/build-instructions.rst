Build instructions
==================

#. Get a local copy of `the code repository <https://github.com/plu5/retype>`_: either clone it or download and extract `ZIP of latest <https://github.com/plu5/retype/archive/main.zip>`_   
#. Install the :doc:`dependencies <dependencies>` [``pip3 install -r requirements.txt``]
#. Install ``pyinstaller`` and ``setuptools`` [``pip3 install pyinstaller setuptools``]
#. Run ``python setup.py b`` and help text will print with the build options you can use. For example, ``python setup.py b -k onedir`` will build retype with pyinstaller in onedir mode.

The output will be in ``/dist``.

Build command options
---------------------

Build options for the ``b`` command:

- ``-k``, ``--kind``: the kind of build to make (out of onedir_, onefile_, hacky_)
- ``-c``, ``--clean``: rm build and dist folders
- ``-x``, ``--xhelp``: show help message and exit. can also be run by running command with no arguments.

  .. note:: ``-h``, ``--help`` will instead show ``setuptools``’s help message.

Build kinds
-----------

onedir
^^^^^^

This is the bog-standard build. The result is a folder with many dependencies in ``dll`` and ``pyd`` files, as well as the retype executable and supporting directories (``library``, ``style``).

This build kind is the safest option.

The downside of this kind of build is a messy resulting folder structure.

Expected output size: 30 MB

onefile
^^^^^^^

In this build all of the dependencies are packed into the executable. The result is a folder with just the retype executable and supporting directories (``library``, ``style``).

.. code-block:: none

   library/
   style/
   retype executable

Additionally, because packing the dependencies into the executable compresses them, the result weighs about 10 MB less than with the other build kinds.

The downside of this kind of build is every time the executable is launched the dependencies packed into the executable need to first be extracted into a temporary directory.

Expected output size: 20 MB

hacky
^^^^^

In this build all of the dependencies are put into a subdirectory, ``include``. It uses a `hook <https://github.com/plu5/retype/blob/main/setup/subdir-hook.py>`_ that adds that directory to sys.path when the program is launched, and a modification of a pyinstaller loader.

For this build to work a modification has to first be made to pyinstaller’s file ``pyimod03_importers.py``. The following line needs to be added after the imports and before ``SYS_PREFIX`` is set:

.. code-block:: python

   sys._MEIPASS = pyi_os_path.os_path_join(sys._MEIPASS, "include")

.. warning:: If you afterwards want to build with other options, you have to first comment out or remove this line.

The result is somewhere in between onedir_ and onefile_; much cleaner resulting directory structure than onedir provides, without the need to extract files every launch.

.. code-block:: none

   include/
   library/
   style/
   base_library.zip
   python37.dll
   retype executable

The obvious downside is it relies on a hack which could stop working or fail to work in certain environments.

Expected output size: 30 MB
