Console
=======

The Console is the input line at the bottom of the screen. Its purpose is twofold:

#. To input console commands, when prefaced with `the prompt <#the-prompt>`_
#. In :doc:`book-view`, to type along to books and advance the cursor

It can be made larger or smaller, or even collapsed, using the drag handle above it.

The prompt
----------

Commands need to be prefaced with the prompt, which is ``>`` by default. :ref:`It can be set to anything <prompt-customisation>`, even an empty string.

.. _console-commands:

Console commands
----------------

This list can also be accessed in retype in the :doc:`about-dialog` and by entering the help console command.

.. jinja:: console_commands

    {% for cmd in commands_info.values() -%}
    {% for alias in cmd.aliases -%}
    ``{{alias}}`` {{'/' if loop.index < cmd.aliases|length else cmd.args or ''}}
    {% endfor %}
       {{cmd.desc}}
    {% endfor -%}

..
   might want to link to the function being called for reference
