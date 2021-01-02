Quick start
===========

Either read the :ref:`installation` instructions or run below commands for Python3.7 under Linux:

.. code-block:: bash

    mkdir libpdf_test
    cd libpdf_test
    python3.7 -m venv .venv
    source .venv/bin/activate
    pip install libpdf[tqdm,colorama]

Then use the command line interface to extract a PDF into a YAML file:

.. code-block:: bash

    libpdf -o output.yaml -f yaml <path to your PDF>

Use ``libpdf --help/-h`` to show the help page with all available options.

For the API usage, create a new file test.py with the content:

.. code-block:: python

    import logging

    import libpdf

    # constrain log levels of pdfminer and PIL to avoid log spam
    logging.getLogger('pdfminer').level = logging.WARNING
    logging.getLogger('PIL').level = logging.WARNING

    # load a PDF with log level set to INFO
    objects = libpdf.load('<path to your PDF>', verbose=2)

Run test.py with a debugger of your choice and inspect the ``objects`` variable.
