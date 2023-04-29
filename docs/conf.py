import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = 'Onionpad'
copyright = '2023, Karsten Lehmann <mail@kalehmann.de>'
author = 'Karsten Lehmann <mail@kalehmann.de>'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.jquery',
]
autodoc_mock_imports = [
    'audiocore',
    'audiomp3',
    'audiopwmio',
    'rotaryio',
    'usb_hid',
    'usb_midi',
]
autodoc_typehints = "both"

intersphinx_mapping = {
    'python': (
        'https://docs.python.org/3',
        None,
    ),
    'CircuitPython': (
        'https://docs.circuitpython.org/en/latest/',
        None,
    ),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_context = {
    'conf_py_path': '/docs/',
    'display_github': True,
    'github_repo': 'onionpad',
    'github_user': 'kalehmann',
    'github_version': 'main',
}
html_static_path = ['_static']
html_theme = 'sphinx_rtd_theme'
