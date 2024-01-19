"""Usage example of libpdf as a library."""

import logging
import sys

import libpdf
from tests.conftest import PDF_LOREM_IPSUM as TEST_PDF

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


def main():
    """Show how the library is used via API."""
    if "tqdm" not in sys.modules:
        # if tqdm is not available, only basic config for logging is initialized.
        # if tqdm is installed the root logger is assigned a custom handler libpdf.log.TqdmLoggingHandler
        # that writes all log messages through tqdm.write() to integrate progress bars with logging
        logging.basicConfig(
            level="DEBUG", format="[%(levelname)5s] %(name)s - %(message)s"
        )

    # constrain log levels of pdfminer and PIL to avoid log spam
    logging.getLogger("pdfminer").level = logging.WARNING
    logging.getLogger("PIL").level = logging.WARNING

    objects = libpdf.load(
        TEST_PDF,
        verbose=3,
        visual_debug=True,
        visual_debug_output_dir="visual_debug",
    )
    LOG.info(objects)


if __name__ == "__main__":
    main()
