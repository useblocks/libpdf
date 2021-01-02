.. role:: underline
    :class: underline

.. only:: html

   .. image:: https://img.shields.io/pypi/l/libpdf.svg
       :target: https://pypi.python.org/pypi/libpdf
       :alt: License
   .. image:: https://img.shields.io/pypi/pyversions/libpdf.svg
       :target: https://pypi.python.org/pypi/libpdf
       :alt: Supported versions
   .. image:: https://readthedocs.org/projects/libpdf/badge/?version=latest
       :target: https://readthedocs.org/projects/libpdf/
   .. image:: https://travis-ci.org/useblocks/libpdf.svg?branch=master
       :target: https://travis-ci.org/useblocks/libpdf
       :alt: Travis-CI Build Status
   .. image:: https://img.shields.io/pypi/v/libpdf.svg
       :target: https://pypi.python.org/pypi/libpdf
       :alt: PyPI Package latest release

.. _pdfplumber: https://github.com/jsvine/pdfplumber
.. _pdfminer: https://github.com/euske/pdfminer

libpdf
======

``libpdf`` allows the extraction of structured data from machine readable PDFs.
It is tested for Python 3.6, 3.7, 3.8 and 3.9.

Motivation
----------

``libpdf`` hopes to bridge the gap between low-level PDF extraction libraries like `pdfminer`_, `pdfplumber`_,
`PyPDF2 <https://github.com/mstamy2/PyPDF2>`_ or `Poppler <https://en.wikipedia.org/wiki/Poppler_(software)>`_
and end users that are looking for a structure and content aware extraction solution.

``libpdf`` specifically cares for the structure of PDFs. It extracts the chapter hierarchy and puts paragraphs,
tables and figures into their corresponding hierarchical position. Extracted PDF links are not just pointing to a
coordinate on a page - as specified in the PDF standard - but to the very chapter/table/figure/paragraph at that
position. That makes it possible to get human and machine readable access to the original document structure.

PDF documents are inherently hard to extract because the PDF standard is optimized for visual representation. PDF does
not know about words, spaces, line breaks or tables. Some libraries are specialized to form words and text lines from
characters and extract that text. However they commonly don't know whether the text is part of a table, inside a figure
or part of a chapter. They also won't recognize headers and footers. That means the user has to post-process the output
and deal with the layout issues.
Libraries like `Camelot <https://github.com/camelot-dev/camelot>`_ or `Tabula <https://github.com/tabulapdf/tabula>`_
are specialized only on table extraction (which is great) and can only be a part of the overall solution.

``libpdf`` implements a well defined :ref:`uml_pdf_model` and populates it with the extracted data.
The API as well as the JSON/YAML output follows the model. The design of the model is
generic and should fit many use cases.

The library is mainly targeted at machine readable technical documentation PDFs, but could also work on others.
Machine readable means the PDF does not consist of bitmaps (so users can select and copy text with a PDF viewer).

After evaluating multiple low-level libraries, `pdfplumber`_ and `pdfminer`_ were chosen as a basis.
Understanding these libraries and their specifics tends to consume a lot of time and resources, so ``libpdf`` was
created to bring users a more ready-to-use experience.

``libpdf`` would not exist without the great underlying libraries and their maintainers' support. Thank you!

Content
-------

.. toctree::
   :maxdepth: 2

   contents/installation
   contents/quickstart
   contents/pdf_model
   contents/concepts_features
   contents/api
   contents/examples
   contents/visual_debugging
   contents/support
   contents/changelog
   contents/license
   contents/authors
   contents/contribution
