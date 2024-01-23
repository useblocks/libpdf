Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

__ https://github.com/useblocks/libpdf/compare/v0.0.1...HEAD

`Unreleased`__
--------------

..
    __ https://github.com/useblocks/libpdf/compare/v0.0.1...v0.0.2

    `0.0.2`__ - 2020-09-30
    ----------------------

Added
~~~~~

- Introduced new element ``Rect`` (`PR #30 <https://github.com/useblocks/libpdf/pull/30>`_)
- Introduced Ruff as linter and formatter (PRs `#28 <https://github.com/useblocks/libpdf/pull/28>`_,
  `#29 <https://github.com/useblocks/libpdf/pull/29>`_ and `#31 <https://github.com/useblocks/libpdf/pull/31>`_)
- Added support for Python 3.10, 3.11 and 3.12 (`PR #27 <https://github.com/useblocks/libpdf/pull/27>`_)

Changed
~~~~~~~

- Updated downstream library dependencies
- Added flag ``--no_annotations`` to exclude annotation extraction from the catalog to speed up extraction
  (`PR #15 <https://github.com/useblocks/libpdf/pull/15>`_)

Removed
~~~~~~~

- libpdf has dropped support for Python 3.6, which reached end-of-life on 2021-12-23; this also fixes the Pillow 8
  security vulnerabilities
- libpdf has dropped support for Python 3.7, which reached end-of-life on 2023-06-27
  (`PR #27 <https://github.com/useblocks/libpdf/pull/27>`_)

Fixed
~~~~~

- Fixed catalog outline title resolve issue (`PR #10 <https://github.com/useblocks/libpdf/pull/10>`_)
- Fixed `duplicate table ID issue #18 <https://github.com/useblocks/libpdf/issues/18>`_
  (`PR #19 <https://github.com/useblocks/libpdf/pull/19>`_)

__ https://github.com/useblocks/libpdf/releases/tag/v0.0.1

`0.0.1`__ - 2020-06-30
----------------------

Added
~~~~~

- Initial version
