Contribution
============

This is an open source project and lives by and with the contribution of the community.
Any help is highly welcome and appreciated:

* testing the library with other PDFs
* reporting bugs or feature requests on `Github <https://github.com/useblocks/libpdf/issues>`_
* uploading a pull request

For code base changes it often makes sense to create a new issue before uploading a pull request.
You can get in touch with the maintainers and agree on the best implementation approach.
Small changes like fixing a typo, contributing to the documentation commonly don't need an issue.

Here are some things worth noting before uploading commits:

* all code must follow the `black <https://black.readthedocs.io/en/stable/>`_ code style
* ruff is used for formatting according to the black style with all defaults
* pull requests are checked using tox
* tox executes (for various Python versions)

    * test cases
    * ruff formatter check
    * ruff linter check
    * the Sphinx documentation build
