Customisation Dialog
====================

The Customisation Dialog allows you to customise many aspects of *retype*. It is saved in file ``config.json`` in the :ref:`user-dir`.

When all the options are set to the same values as they are in the config, the Revert button is greyed out. When you change them it will be clickable and allows you to revert to the saved values. In order to save changed settings, the Save button must be pressed. After doing so, the Revert button will be greyed out again since the options values match the saved ones again.

When the options are set to the same values as the default config, the Restore Defaults button is greyed out. When you change them, it will be clickable and allows you to revert to the default values. In order to return to the default values, the Save button must be pressed after clicking Restore Defaults.

Paths
-----

.. _user-dir:

User dir
^^^^^^^^

Path to the user dir, which is where the save and config files are stored.

.. _library-search-paths:

Library search paths
^^^^^^^^^^^^^^^^^^^^

Paths where *retype* should look for epub files.

Console
-------

.. _prompt-customisation:

Prompt
^^^^^^

The prompt is a string console commands must be prefixed by. Can be any length, including an empty string if you do not want to prefix them with anything.

.. _skip-char-key:

Skip character key
^^^^^^^^^^^^^^^^^^

When enabled, pressing the configured key while typing will skip the current character forward, advancing the cursor by one position without having to type the character. This is useful for getting past characters you cannot easily input.

The feature is disabled by default. To enable it, check the :guilabel:`Enable skip character key binding` checkbox. Once enabled, the key field below it becomes active and can be set by clicking on it and pressing the desired key. The default key is :kbd:`Tab`.

The skip character action can also be triggered at any time via the :ref:`console-commands` using the ``skipchar`` command (aliases: ``char``, ``c``).

Hide System Console window on UI load (Windows-only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On Windows, applications can be built in either console or windowed mode. The downside of the latter is you get no debug output even if you run it from a terminal. Therefore, *retype* is built in console mode, but in order to prevent the console window from getting in the users way, it is by default hidden when the UI loads. This checkbox enables you to disable this, if you prefer the console window to remain visible.

You can toggle the console window at any time by clicking on the menu option ``View > Toggle System Console``.

Blender users will be familiar with this concept.

.. note::
   Hiding the console window is only possible if *retype* was built with ``pywin32``.

Book View
---------

Font size
^^^^^^^^^

The font size can be saved on quit or set to a constant default.

The font size can be changed at any time in :doc:`book-view` using the :ref:`toolbar-actions` or using the mousewheel while holding :kbd:`Ctrl`.

.. _replacements:

Replacements
------------

Configure substrings that can be typeable by any one of the set comma-separated list of replacements. This is useful for unicode characters that you don’t have an easy way to input. Each replacement should be of equal length to the original substring. 

Window Geometry
---------------

The window geometry can be saved on quit or set to a constant default.

The state of the splitters can be saved on quit. This refers to the position of the drag handle above the :doc:`console` and :ref:`stats-dock`; their size and whether they should be collapsed or not.
