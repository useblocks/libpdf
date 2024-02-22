"""
Workaround to deliver forked dependencies with libpdf.

PyPI repository does not allow uploading packages that have direct Git dependencies (400 Bad Request returned).
This should be resolved in future by

* releasing the forked libraries on PyPI on ourselves with a different name
* raising PRs for upstream merges (best approach)

These 2 methods take time, so below solution is a short-term workaround.
"""

import os
import sys

DEPS_DIR = os.path.join(os.path.dirname(__file__), "..", "deps")

# first try to import the dependencies so active venvs with direct Git dependencies are not overriden
try:
    import pdfminer
except ModuleNotFoundError:
    # make dependency available as wheel to sys.path as first entry
    sys.path.insert(
        0, os.path.join(DEPS_DIR, "pdfminer.six-20200517.dev1-py3-none-any.whl")
    )
else:
    del pdfminer

try:
    import pdfplumber
except ModuleNotFoundError:
    sys.path.insert(
        0, os.path.join(DEPS_DIR, "pdfplumber-0.5.21.dev1-py3-none-any.whl")
    )
else:
    del pdfplumber
