Build docs locally
==================

#. :doc:`Download retype sources and required dependencies <running-from-sources>`
#. Install ``Sphinx`` and ``sphinx-rtd-theme``
#. cd into the ``docs`` folder
#. Run ``make html``, or on Windows ``./make.bat html``
#. If build succeeds, open ``build/html/index.html`` in your browser

Between builds you may sometimes have to ``make clean`` for things to work properly, for example when updating public files like images or css.

There are a few things that don’t seem to work locally, that do work on readthedocs:

- No twisties to open subsections in the sidebar
- When you navigate to another section or subsection, the sidebar does not automatically scroll to where you were
