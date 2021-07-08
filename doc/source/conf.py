# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import locale
import subprocess
from pathlib import Path
from fnmatch import fnmatch

DOC_SOURCE = Path(__file__).parent
DOC_ROOT = DOC_SOURCE.parent.absolute()
REPO_ROOT = DOC_ROOT.parent.absolute()
PACKAGE_DIR = (REPO_ROOT / 'datadings').absolute()
sys.path.insert(0, str(REPO_ROOT.absolute()))


# -- Project information -----------------------------------------------------

project = 'datadings'
copyright = '2021, Joachim Folz'
author = 'Joachim Folz'


# -- Setup -------------------------------------------------------------------


def __get_helptext(modname):
    enc = locale.getpreferredencoding() or sys.stdout.encoding or 'utf-8'
    env = dict(
        os.environ,
        DOCSBUILD='true',
    )
    return subprocess.check_output(
        [sys.executable, '-m', modname, '-h'],
        stderr=subprocess.STDOUT,
        encoding=enc,
        cwd=REPO_ROOT,
        env=env,
    )


def __make_helptext_nice(helptext):
    return helptext \
        .replace('Note:', '.. note::') \
        .replace('See also:', '.. seealso::') \
        .replace('Important:', '.. important::') \
        .replace('positional arguments:', 'Positional arguments\n^^^^^^^^^^^^^^^^^^^^\n') \
        .replace('optional arguments:', 'Optional arguments\n^^^^^^^^^^^^^^^^^^\n')


def autodoc_process_docstring(app, what, name, obj, options, lines):
    """
    Replace the parsed docstring with the actual help text of the script.
    """
    if what == 'module' and (
        fnmatch(name, 'datadings.commands.*') or
        fnmatch(name, 'datadings.sets.*_write')
    ):
        lines.clear()
        helptext = __get_helptext(name)
        helptext = __make_helptext_nice(helptext)
        lines.extend(helptext.splitlines())
        lines.append('')


def setup(app):
    app.connect('autodoc-process-docstring', autodoc_process_docstring)
    env = dict(
        os.environ,
        SPHINX_APIDOC_OPTIONS='members,show-inheritance,undoc-members',
    )
    subprocess.check_call([
            sys.executable,
            '-m', 'sphinx.ext.apidoc',
            '--module-first',
            '--separate',
            '--maxdepth', '6',
            '--no-toc',
            '--output-dir', str(DOC_SOURCE / 'generated'),
            str(PACKAGE_DIR),
        ],
        env=env,
    )
    os.remove(DOC_SOURCE / 'generated' / 'datadings.rst')


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    # 'sphinx_autodoc_typehints',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# location of index.rst
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_logo = '_static/datadings512.png'

html_css_files = [
    'custom.css',
]

# Config for sphinx-rtd-theme
html_theme_options = {
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 5,
    'includehidden': False,
    'titles_only': False
}

# -- Other -------------------------------------------------------------------

# Add Python doc to intersphinx
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'natsort': ('https://natsort.readthedocs.io/en/master/', None),
}

# autodoc Configuration
autoclass_content = 'class'
autodoc_docstring_signature = True
autodoc_typehints = 'signature'
# autodoc_mock_imports = ["augpy._augpy"]

# avoid clashing labels between C++ and Python
autosectionlabel_prefix_document = True

# enable napoleon types for undocumented params
always_document_param_types = True

# napoleon config
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_keyword = True
napoleon_include_init_with_doc = True
