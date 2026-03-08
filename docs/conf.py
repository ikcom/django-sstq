import sys
from pathlib import Path

# Setup Django settings for Sphinx documentation

sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "django-sstq"
copyright = "2026, Ilir Kokollari"
author = "Ilir Kokollari"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinxcontrib_django",
]
templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_permalinks_icon = "<span>#</span>"
html_theme = "furo"
html_title = project


intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", None),
}

nitpick_ignore = [
    ("py:class", "P"),
    ("py:class", "R"),
    ("py:class", "T"),
    ("py:obj", "typing.P"),
    ("py:obj", "typing.R"),
    ("py:obj", "typing.T"),
    ("py:class", "django.db.models.enums.IntegerChoices"),  # Django internal not in intersphinx
]

html_static_path = ["_static"]
html_css_files = ["style.css"]

django_settings = "testconf.settings"
