.. _installation:

Installation
============

The package is managed with `Poetry <https://github.com/python-poetry/poetry>`_.

Using pip
---------

You may want to install ``libpdf`` and its dependencies into a virtual environment. Activate it like this for
Python 3.7 under Linux:

.. code-block:: bash

    python3.7 -m python3.7 -m venv venv
    source venv/bin/activate

You may alternatively install ``libpdf`` into your user's home directory using the pip ``--user`` option instead.

pip understands the pyproject.toml standard, so ``libpdf`` can be installed using pip:

.. code-block:: bash

    pip install libpdf

If you wanna get fancy colored progress bars, install also the extra dependencies:

.. code-block:: bash

    pip install libpdf[tqdm,colorama]

Using sources
-------------

The pip ``-e, --editable`` option does `not yet support pyproject.toml <https://github.com/pypa/pip/issues/6434>`__
files.
However the editable mechanism is `now the Poetry default <https://github.com/python-poetry/poetry/issues/34>`__  when
running ``poetry install`` on the source directory.

Install ``poetry`` either via ``pip install --user poetry`` to your home directory or into a virtual environment.
Then clone the ``libpdf`` repo and install it with its dependencies:

.. code-block:: bash

    git clone https://github.com/useblocks/libpdf
    cd libpdf
    poetry install

``libpdf`` optionally supports progress bars. They rely on ``tqdm`` and ``colorama``.
To get them also install the extra dependencies:

.. code-block:: bash

    poetry install -E tqdm -E colorama

``tqdm`` provides the progress bars and ``colorama`` colors them beautifully. Installing only ``tqdm`` is also possible,
progress bars will be shown in default terminal color. If both libraries are not installed, ``libpdf`` will
gracefully fall back to a reasonable amount of log messages.

.. note:: Poetry will use any pre-activated virtual environments. If none is active, it will create one.
