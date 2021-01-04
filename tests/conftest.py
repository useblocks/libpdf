"""Pytest conftest module containing common test configuration and fixtures."""
import os

from libpdf import load

import pytest

# test PDFs from pdfplumber
PDF_LOREM_IPSUM = os.path.join(os.path.dirname(__file__), 'pdf', 'lorem-ipsum.pdf')
PDF_TWO_COLUMNS = os.path.join(os.path.dirname(__file__), 'pdf', 'two_colums_sampe.pdf')
PDF_WITH_EMPTY_OUTLINE = os.path.join(os.path.dirname(__file__), 'pdf', 'issue-67-example.pdf')
PDF_OUTLINE_NO_DEST = os.path.join(os.path.dirname(__file__), 'pdf', 'pdffill-demo.pdf')
PDF_FIGURE_WITH_INVALID_BBOX = os.path.join(os.path.dirname(__file__), 'pdf', 'pr-138-example.pdf')
PDF_CHAPTER_DETECTION = os.path.join(os.path.dirname(__file__), 'pdf', 'DS93-chapter-issue-fix.pdf')

# full features PDF
PDF_FULL_FEATURES = os.path.join(os.path.dirname(__file__), 'pdf', 'full_features.pdf')
PDF_FIGURES_EXTRACTION = os.path.join(os.path.dirname(__file__), 'pdf', 'test_figures_extraction.pdf')
PDF_SMART_HEADER_FOOTER_DETECTION = os.path.join(os.path.dirname(__file__), 'pdf', 'test_header_footer_detection.pdf')


def obj_equal(class_type, instance1, instance2):
    """
    Do a attribute based comparison of instances.

    :param class_type: both instances must be of this type
    :param instance1: first object
    :param instance2: second object
    :return: True if all attributes are equal else False
    """
    if not isinstance(instance1, class_type) or not isinstance(instance2, class_type):
        # don't attempt to compare against unrelated types
        return NotImplemented

    # get attributes of each and exclude special names and back references
    self_attr = [attr for attr in dir(instance1) if (not attr.startswith('__') and not attr.startswith('b_'))]
    other_attr = [attr for attr in dir(instance2) if (not attr.startswith('__') and not attr.startswith('b_'))]
    if set(self_attr) == set(other_attr):
        for attr in self_attr:
            if getattr(instance1, attr) != getattr(instance1, attr):
                # TODO this uses the equality operator which might fail for referred elements like page on Position
                return False
        return True
    return False


@pytest.fixture(scope='session')
def load_full_features_pdf(tmpdir_factory, request):
    """Load test pdf and return temporary directory path and the libpdf object."""
    tmpdir = tmpdir_factory.mktemp('full_features_pdf')
    tmpdir_path = str(tmpdir)
    save_figures = request.param if hasattr(request, 'param') else False
    return tmpdir_path, load(
        PDF_FULL_FEATURES,
        save_figures=save_figures,
        figure_dir=os.path.join(tmpdir_path, 'figures'),
    )
