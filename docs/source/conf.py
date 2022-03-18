# Configuration file for the Sphinx documentation builder.

import os
import sys


proj_path = os.path.abspath('../..')
sys.path.insert(0, proj_path)


from retype.console.command_service import commands_info  # noqa: E402


docs_path = os.path.join(proj_path, 'docs')
static_path = os.path.join(docs_path, '_static')
img_path = os.path.join(static_path, 'img')

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# -- Project information

project = 'retype'
version = release = '1.0.0'
copyright = 'none (Public Domain)'

rst_epilog = """.. |Version| replace:: %s""" % version

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx_jinja',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

jinja_contexts = {
    'console_commands': {'commands_info': commands_info},
}

templates_path = [os.path.join(docs_path, '_templates')]
exclude_patterns = ['_build', '_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'
html_static_path = [static_path]
html_logo = os.path.join(img_path, "docs_logo.png")
html_favicon = os.path.join(img_path, "retype.ico")

html_css_files = [
    "css/custom.css",
]

html_theme_options = {
    "collapse_navigation": False,
}

# -- Options for EPUB output

epub_show_urls = 'footnote'
