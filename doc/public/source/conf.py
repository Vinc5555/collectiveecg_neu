# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Heart_sync'
copyright = '2025, Julien Karadayi, Victor Chung,'
author = 'Julien Karadayi, Victor Chung,'
release = 'V1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
 
extensions = [
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
    'sphinx.ext.imgmath',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
    'myst_parser'
]
 
autodoc_inherit_docstrings = True
autodoc_default_options = {
    'member-order': 'bysource',
    'show-inheritance': True,
    'undoc-members': True,
}
 
# -- Napoleon options --------------------------------------------------------
# http://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_rtype = False
 
templates_path = ['_templates']
exclude_patterns = []
 
 
 
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
 
html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']

## -- General configuration ---------------------------------------------------
## https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
#
#extensions = [
#    ...
#    'sphinx.ext.autodoc',
#]
#templates_path = ['_templates']
#exclude_patterns = []
#
#
#
## -- Options for HTML output -------------------------------------------------
## https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
#
#html_theme = 'alabaster'
#html_static_path = ['_static']
