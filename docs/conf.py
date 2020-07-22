"""Configuration file for the Sphinx documentation builder."""

# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os

# -- Project information -----------------------------------------------------

project = 'libpdf'
copyright = '2020, team useblocks'  # noqa: A001 (python builtin)
author = 'team useblocks'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinxcontrib.plantuml',
]


# Plantuml configuration
cwd = os.getcwd()
plantuml = 'java -jar {}'.format(os.path.join(cwd, 'utils/plantuml.jar'))
# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
# exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


def remove_module_docstring(app, what, name, obj, options, lines):
    """
    Remove certain unwanted module docstrings for Sphinx output.

    Invoked by Sphinx event autodoc-process-docstring.
    Original idea from https://stackoverflow.com/a/18031024.
    """
    if what == 'module' and name == 'libpdf':
        del lines[:]


def setup(app):
    """Add custom parts to the Sphinx app."""
    # Option to remove certain unwanted module docstrings for autodoc automodule directive
    app.connect('autodoc-process-docstring', remove_module_docstring)

    # Add a custom CSS class that expands the theme CSS rules
    app.add_css_file('mystyle.css')


# -- Options for autodoc -------------------------------------------------
autodoc_typehints = 'description'
autodoc_default_options = {
    'member-order': 'bysource',
    'members': True,
    'exclude-members': 'set_backref, set_position_backref, contains_coord, set_cells_backref',
    'undoc-members': True,
    'show-inheritance': True,
}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages. See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    # TOC options
    'collapse_navigation': False,
    'sticky_navigation': False,
    'navigation_depth': 7,
    # content options
    'prev_next_buttons_location': None,
}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#
html_logo = '_static/libpdf_simple.svg'

# The name of an image file (relative to this directory) to use as a favicon of
# the docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#
html_favicon = '_static/libpdf_favicon_simple.ico'
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
