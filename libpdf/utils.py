"""Helper functions."""
import logging
import os
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type, Union

import chardet

from libpdf.log import logging_needed
from libpdf.models.chapter import Chapter
from libpdf.models.element import Element
from libpdf.models.figure import Figure
from libpdf.models.paragraph import Paragraph
from libpdf.models.table import Table
from libpdf.parameters import RENDER_ELEMENTS, VIS_DBG_MAP_ELEMENTS_COLOR
from libpdf.progress import bar_format_lvl1, tqdm

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import (
    LAParams,
    LTAnno,
    LTChar,
    LTCurve,
    LTFigure,
    LTImage,
    LTLine,
    LTPage,
    LTRect,
    LTText,
    LTTextBox,
    LTTextBoxHorizontal,
    LTTextLineHorizontal,
)
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

import pdfplumber

MAP_TYPES = {
    Chapter: 'chapter',
    Paragraph: 'paragraph',
    Table: 'table',
    Figure: 'figure',
    LTChar: 'paragraph',
    LTCurve: 'figure',
    LTTextBox: 'paragraph',
    LTTextBoxHorizontal: 'paragraph',
    LTTextLineHorizontal: 'paragraph',
    LTFigure: 'figure',
    LTLine: 'figure',
    LTRect: 'figure',
    LTImage: 'figure',
}

LOG = logging.getLogger(__name__)


def decode_title(obj_bytes: bytes) -> str:
    """Decode catalog headline using chardet library."""
    chardet_ret = chardet.detect(obj_bytes)
    try:
        str_ret = obj_bytes.decode(chardet_ret['encoding'])
    except UnicodeDecodeError:
        str_ret = obj_bytes.decode(chardet_ret['encoding'], 'backslashreplace')
        LOG.warning(
            'Could not fully decode catalog headline "%s". Replaced character(s) with escaped hex value.',
            str_ret,
        )
    return str_ret


def create_out_dirs(src_file, *paths):
    r"""
    Create paths relative to the directory of src_file and return the target directory.

    The function calculates the basedir from the file path given in src_path and
    joins it with the given \*paths.
    Example call: ``create_out_dirs(__name__, 'output', 'visual_debug')``.

    :param src_file: base path given as file path, it's supposed to be set to __file__ by the caller
    :param paths: list of paths to be appended
    :return: created directory path
    """
    basedir = os.path.dirname(os.path.realpath(src_file))
    target_dir = os.path.join(basedir, *paths)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    return target_dir


def string_to_identifier(text: str):
    r"""
    Take an input text and return an identifier.

    The function replaces characters not allowed in identifiers with underscores.
    This is the Python definition of an identifier::

        identifier ::=  (letter|"_") (letter | digit | "_")*
        letter     ::=  lowercase | uppercase
        lowercase  ::=  "a"..."z"
        uppercase  ::=  "A"..."Z"
        digit      ::=  "0"..."9"

    If the identifier starts with a digit after the replacing operation, an underscore is prepended.
    In case the input text contains a newline sequence, an exception is thrown.
    :param text: the input text
    :raises: ValueError: text contains newline chars \r or \n
    :return: identifier
    """
    newline_chars = ['\r', '\n']
    for newline_char in newline_chars:
        if newline_char in text:
            raise ValueError(f'Input text "{text}" contains a new line character.')
    allowed_chars_regex = re.compile(r'[^_a-zA-Z0-9]')
    replace_string = allowed_chars_regex.sub('_', text)
    if replace_string[0].isdigit():
        replace_string = '_' + replace_string
    return replace_string


def to_pdfplumber_bbox(x0, y0, x1, y1, page_height):
    """
    Convert PDF standard or pdfminer bbox coordinates to pdfplumber bbox coordinates.

    The function is needed because for pdfplumber:
    - y coordinates are inverted
    - Decimal type is needed

    Some diagram may help::

        PDF standard and pdfminer bbox               pdfplumber bbox
        *-page------------------------*              *-page------------------------*
        |                             |              |                ^      ^     |
        |                             |              |               top     |     |
        |                             |              |                v      |     |
        |        +-bbox----+          |              |        +-bbox----+    |     |
        |<--x0-->|         |    ^     |              |<--x0-->|         |    |     |
        |        |         |    |     |              |        |         |  bottom  |
        |<-------|---x1--->|    |     |              |<-------|---x1--->|    |     |
        |        +---------+    |     |              |        +---------+    v     |
        |            ^          |     |              |                             |
        |           y0         y1     |              |                             |
        |            v          v     |              |                             |
        *-----------------------------*              *-----------------------------*
        pdfminer   sees y0 and y1 from the bottom of the page
        pdfplumber sees y0 and y1 from the top of the page

    The input parameter must be given as specified in PDF standard and pdfminer.

    :param x0: the distance from the left of the page to the left edge of the box
    :param y0: the distance from the bottom of the page to the lower edge of the box
    :param x1: the distance from the left of the page to the right edge of the box
    :param y1: the distance from the bottom of the page to the upper edge of the box
    :param page_height: height of the page
    :return: [x0, top, x1, bottom]
    """
    # pylint: disable=invalid-name  # short is better here
    ret_x0 = Decimal(x0)
    ret_y0 = Decimal(Decimal(page_height) - Decimal(y1))
    ret_x1 = Decimal(x1)
    ret_y1 = Decimal(Decimal(page_height) - Decimal(y0))
    return [ret_x0, ret_y0, ret_x1, ret_y1]


def from_pdfplumber_bbox(x0, top, x1, bottom, page_height):
    """
    Convert pdfplumber bbox coordinates to PDF standard.

    :param x0: the distance from the left of the page to the left edge of the box
    :param top: the distance from the top of the page to the upper edge of the box
    :param x1: the distance from the left of the page to the right edge of the box
    :param bottom: the distance from the top of the page to the lower edge of the box
    :param page_height: height of the page
    :return: [x0, y0, x1, y1]
    """
    # pylint: disable=invalid-name  # short is better here
    return [float(x0), float(page_height - bottom), float(x1), float(page_height - top)]


def check_lt_obj_in_bbox(lt_obj, bbox: Tuple[float, float, float, float]):
    """
    Check if pdfminer LTContainer layout object (lt_obj) is completely inside the given bounding box (bbox).

    Examples::

        Returns False                           Returns True
        +--lt_page------------------------+     +-lt_page------------------------+
        |                  +--bbox---+    |     |        +--------bbox-------+   |
        |                  |         |    |     |        |                   |   |
        |  +--lt_obj---+   |         |    |     |        |   +---lt_obj----+ |   |
        |  |           |   +---------+    |     |        |   |             | |   |
        |  |           |                  |     |        |   |             | |   |
        |  |           |                  |     |        |   |             | |   |
        |  +-----------+                  |     |        |   +-------------+ |   |
        |                                 |     |        +-------------------+   |
        +---------------------------------+     +--------------------------------+

        Returns False
        +--lt_page------------------------+
        |            +--bbox---+          |
        |            |         |          |
        |  +--lt_obj---+       |          |
        |  |         | |       |          |
        |  |         +-|-------+          |
        |  |           |                  |
        |  +-----------+                  |
        |                                 |
        +---------------------------------+

    :param lt_obj: pdfminer layout object
    :param bbox: given bounding box, a rectangle area
    :return: True if lt_obj is completely containd in bbox else False
    """
    lt_obj_in_bbox = False
    if lt_obj.x0 > bbox[0] and lt_obj.y0 > bbox[1] and lt_obj.x1 < bbox[2] and lt_obj.y1 < bbox[3]:
        lt_obj_in_bbox = True

    return lt_obj_in_bbox


def find_lt_obj_in_bbox(
    lt_objs_in_bbox: List,
    lt_obj,
    bbox: Tuple[float, float, float, float],
):  # pylint: disable=too-many-nested-blocks, too-many-branches  # local algorithm, easier to read when not split up
    """
    Find all layout objects (lt_obj) inside given bounding box (bbox) recursively.

    The pdfminer LTComponent layout object lt_obj is hierarchical, so a subset of the hierarchy can be contained in the
    bbox. The function will add the highest level hierarchical elements that are fully contained in the bbox to the list
    lt_objs_in_bbox. The function is recursive and the in/out parameter lt_objs_in_bbox is passed around and populated.

    Examples::

        lt_objs_in_bbox = [lt_obj]
        +-------bbox-----+
        |                |
        |  +-lt_obj--+   |
        |  |         |   |
        |  |         |   |
        |  +---------+   |
        |                |
        |                |
        +----------------+

        lt_objs_in_bbox = [LTTextBoxHorizontal1, LTTextBoxHorizontal2]
                   +----bbox-------------------------+
                   |                                 |
        +-lt_obj---|--------------------------+      |
        |          | +-LTTextBoxHorizontal1-+ |      |
        | +-LT0-+  | |                      | |      |
        | |     |  | +----------------------+ |      |
        | +-----+  |                          |      |
        |          | +-LTTextBoxHorizontal2-+ |      |
        |          | |                      | |      |
        |          | +----------------------+ |      |
        +----------|--------------------------+      |
                   |                                 |
                   +---------------------------------+

        lt_objs_in_bbox = []
                        +--bbox---+
                        |         |
        +--lt_obj---+   |         |
        |           |   +---------+
        |           |
        |           |
        +-----------+

    If a layout object is partially inside the given bounding box (bbox), then the function will recurse and
    search for lower level layout objects completely inside the bbox.

    The pdfminer LTAnno class doesn't have any position metadata, it's a virtual space character that pdfminer
    adds between 2 LTChar objects to denote word boundaries. Any trailing LTAnno is considered zero-width and
    always contained in the given bbox. Trailing LTAnno may be deleted in a post-processing step.

    :param lt_objs_in_bbox: list of LTComponent objects inside given bounding box
    :param lt_obj: LTComponent object like LTTextBox, LTLine, LTTextLine
    :param bbox: a given bounding box
    :return: None
    """
    if check_lt_obj_in_bbox(lt_obj, bbox):
        # This is the case when a LT object is fully inside the given bounding box
        lt_objs_in_bbox.append(lt_obj)
    elif (
        lt_obj.x1 < bbox[0]  # lt_obj completely left of bbox
        or lt_obj.x0 > bbox[2]  # lt_obj completely right of bbox
        or lt_obj.y1 < bbox[1]  # lt_obj completely below bbox
        or lt_obj.y0 > bbox[3]  # lt_obj completely above bbox
    ):
        # This is the case when a LT object is neither inside nor intersected with the given bounding box.
        pass
    else:
        # This is the case when a LT object is intersected with the given box. In this case, the LT objects inside the
        # given bounding box need to be hierarchically and recursively found.
        if hasattr(lt_obj, '_objs'):
            # All the downwards hierarchical LT objects are stored in the attribute "_objs".
            # If the _objs attribute doesn't exist, it means it's the bottom of the hierarchy.
            text_inside_bbox = False  # True on LTTextLine level when the first LTChar is inside the BBOX
            for item in lt_obj._objs:  # pylint: disable=protected-access
                if isinstance(item, LTAnno):
                    # special treatment of LTAnno because it is virtual with no position data
                    if text_inside_bbox:
                        # LTAnno is added because an LTChar was inside the bbox before
                        lt_objs_in_bbox.append(item)
                else:
                    if isinstance(item, LTChar):
                        # check if the first and last LTChar have shown in the given bbox to decide if the trailing
                        # LTAnno should be added
                        ltchar_inside = check_lt_obj_in_bbox(item, bbox)
                        if text_inside_bbox:
                            if ltchar_inside:
                                lt_objs_in_bbox.append(item)
                            else:
                                # the bbox just ended and can't enter again
                                break
                        else:
                            if ltchar_inside:
                                lt_objs_in_bbox.append(item)
                                text_inside_bbox = True
                            else:
                                # no LTChar was added before, so not in BBOX yet
                                pass
                    else:
                        # it is not an LTAnno nor an LTChar, so recurse and break it further down
                        find_lt_obj_in_bbox(lt_objs_in_bbox, item, bbox)
        else:
            # no attribute "_objs" exists. It reaches the bottom of the hierarchy
            pass


def page_crop(
    bbox: Tuple[float, float, float, float],
    lt_objs: List,
    lt_type_in_filter: Type[Union[LTText, LTCurve, LTImage, LTFigure]],
    contain_completely: bool = False,
) -> List:
    """
    Find and filter pdfminer layout objects in the given bounding box.

    The pdfminer layout analysis algorithm works as follows:

    grouping characters into textlines: LTChar/LTAnno --> LTTextline
    grouping textlines into boxes: LTTextLine --> LTTextBox

    Hence, there are three different levels of elements in each LTPage:

    1. LTTextBox, LTFigure, LTLine, LTImage, LTRect
    2. LTTextLine, LTCurve
    3. LTChar, LTAnno

    This function filters LT objects according to the whitelist. LTImage and LTFigure extract the objects as their
    literal name, while LTText and LTCurve are explained below.

    LTText:
    When LTText is in the whitelist, LTAnno, LTChar, LTTextLine and LTTextbox objects will be returned since LTText is
    an interface class inherited by text-related classes, LTAnno, LTTextline and LTTextbox. These text-related objects
    are able to be merged by the function which takes care of the merge.

    LTCurve:
    LTCurve is inherited by LTLine and LTRect. When LTCurve is set in the whitelist, LTCurve, LTLine and LTRect will be
    collected. These drawing-related objects can be used further for users who would like to do
    table or figure analysis.


    :param bbox: bounding box, rectangular area [x0, y0, x1, y1]
    :param lt_objs: A list of pdfminer layout elements on a page
    :param lt_type_in_filter: a type filter of LTItem from pdfminer
    :param contain_completely: If the flag is true, the hierarchy is kept
    :return: a list of LT objects, which has been filtered with whitelist
    """
    # find layout object lt_obj inside the given bbox
    # by comparing lt_obj.bbox with given bbox
    lt_objs_in_bbox = []
    for element in lt_objs:
        if isinstance(element, lt_type_in_filter):
            # find lt_obj inside bbox, update to the list
            if contain_completely:
                if check_lt_obj_in_bbox(element, bbox):
                    lt_objs_in_bbox.append(element)
            else:
                find_lt_obj_in_bbox(lt_objs_in_bbox, element, bbox)

    return lt_objs_in_bbox


def textbox_crop(
    bbox: Tuple[float, float, float, float],
    ltpage_objs: List,
    word_margin: float,
    y_tolerance: float,
) -> Union[LTTextBoxHorizontal, None]:
    """
    Collect and group all LTChar in a given bbox and return only one LTTextBoxHorizontal.

    :param bbox: a given bounding box (x0, y0, x1, y1)
    :param ltpage_objs: a list of LT objects in a cetain LTPage
    :param word_margin: pdfminer laparam for word margins in a LTTextline
    :param y_tolerance: the vertical tolerance to group a line. LTAnno with newline is inserted at the end of a line
    :return: a LTTextbox or None if no LTChar in the given bbox
    """
    lt_objs = page_crop(bbox, ltpage_objs, LTText)
    if len(lt_objs) == 0:
        # None of LTText objects exists
        return None
    if len(lt_objs) == 1:
        if isinstance(lt_objs[0], LTTextBoxHorizontal):
            # only one LTTextbox completely inside the given bbox
            return lt_objs[0]

    flatten_lt_objs = []
    flatten_hiearchical_lttext(lt_objs, flatten_lt_objs)
    lt_textlines = assemble_to_textlines(flatten_lt_objs, word_margin, y_tolerance)

    if lt_textlines:
        lt_textbox = LTTextBoxHorizontal()
        for textline in lt_textlines:
            lt_textbox.add(textline)

        return lt_textbox

    return None


def assemble_to_textlines(
    flatten_lt_objs: List[LTText],
    word_margin: float,
    y_tolerance: float,
) -> List[LTTextLineHorizontal]:
    """
    Assemble all LTChar into a LTTextline or several LTTextlines.

    The flatten_lt_objs is a list of LTChar and LTAnno which are already sorted because layout analysis of pdfminer
    sort each LTTextboxHorizontal from top to bottom. When the hierarchical structure is flatten, LTChar and LTAnno are
    placed in the order of their x coordinates by textlines

    These LTChar are groupped into textlines again in the scope of only one textbox. words-grouping is still made by
    pdfminer layout analysis, but the textlines-grouping is according to the vertical center of each character.

    :param flatten_lt_objs: a list of LTChar and LTAnno
    :param word_margin: pdfminer laparam for word margins in a LTTextline
    :param y_tolerance: the vertical tolerance to group a line. LTAnno with newline is inserted at the end of a line
    :return: a list of LTTextline
    """
    lt_textlines = [LTTextLineHorizontal(word_margin)]
    if isinstance(flatten_lt_objs[0], LTChar):
        last_ltobj = flatten_lt_objs[0]
    else:
        last_ltobj = flatten_lt_objs[1]

    for lt_obj in flatten_lt_objs:
        if isinstance(lt_obj, LTChar):
            if abs((lt_obj.y0 + (lt_obj.height / 2)) - (last_ltobj.y0 + (last_ltobj.height / 2))) < y_tolerance:
                lt_textlines[-1].add(lt_obj)
            else:
                lt_textlines[-1]._objs.append(LTAnno('\n'))  # pylint: disable=protected-access # access needed
                lt_textlines.append(LTTextLineHorizontal(word_margin))
                lt_textlines[-1].add(lt_obj)

            last_ltobj = lt_obj

    return lt_textlines


def flatten_hiearchical_lttext(lt_objs: List[LTText], flatten_lt_objs: List[LTChar]):
    """
    Flatten hierarchical LTText which can be LTTextBox and LTLine.

    The flatten LT objects are stored in the list 'flatten_lt_objs'

    :param lt_objs: a list of hierarchical LT objects, which may be LTTextbox, LTTextline, LTChar, or LTAnno
    :param flatten_lt_objs:  a list of LT objects in a flatten structure, where the results are stored
    :return:
    """
    for lt_obj in lt_objs:
        if isinstance(lt_obj, (LTTextBoxHorizontal, LTTextLineHorizontal)):
            if hasattr(lt_obj, '_objs'):
                flatten_hiearchical_lttext(
                    lt_obj._objs,  # pylint: disable=protected-access  # not publicly available
                    flatten_lt_objs,
                )
        elif isinstance(lt_obj, (LTChar, LTAnno)):
            flatten_lt_objs.append(lt_obj)


def get_elements_on_page(elements: List[Element], page_no, element_type=None):
    """
    Return all libpdf elements that are on a certain page.

    :param elements: list of elements
    :param page_no: page number
    :param element_type: filter elements for this type
    :return: list of elements on the given page
    """
    page_elements = []
    for element in elements:
        if element_type is not None:
            if not isinstance(element, element_type):
                continue
        if element.position.page.number == page_no:
            page_elements.append(element)
    return page_elements


def visual_debug_libpdf(  # pylint: disable=too-many-branches
    objects,
    visual_output_dir,
    visual_split_elements,
    visual_debug_include_elements,
    visual_debug_exclude_elements,
):
    """Visual debug."""
    LOG.info('Starting visual debug...')
    # collect all elements
    all_elements = (
        objects.flattened.chapters + objects.flattened.paragraphs + objects.flattened.tables + objects.flattened.figures
    )

    # prepare for calling the common draw and output function
    draw_elements = {}
    for page in tqdm(objects.root.pages, desc='###### Calculating bboxes', unit='pages'):
        page_elements = get_elements_on_page(all_elements, page.number)
        for page_element in page_elements:
            draw_element = {
                'element': page_element,
                'x0': page_element.position.x0,
                'y0': page_element.position.y0,
                'x1': page_element.position.x1,
                'y1': page_element.position.y1,
            }
            if page.number not in draw_elements:
                draw_elements[page.number] = [draw_element]
            else:
                draw_elements[page.number].append(draw_element)

    LOG.info('Rendering images')

    if visual_debug_include_elements:
        rendered_elements = visual_debug_include_elements
    elif visual_debug_exclude_elements:
        rendered_elements = set(RENDER_ELEMENTS) - set(visual_debug_exclude_elements)
    else:
        # default rendering all elements
        rendered_elements = RENDER_ELEMENTS

    if rendered_elements:
        if visual_split_elements:
            # rendering elements to separate folder
            for render_element in rendered_elements:
                target_dir = os.path.join(visual_output_dir, render_element)
                Path(target_dir).mkdir(parents=True, exist_ok=True)
                render_pages(
                    pdf_pages=objects.pdfplumber.pages,
                    target_dir=target_dir,
                    name_prefix='libpdf_',
                    draw_elements=draw_elements,
                    render_elements=[render_element],
                )
        else:
            # rendering elements together under visual_output_dir
            Path(visual_output_dir).mkdir(parents=True, exist_ok=True)
            render_pages(
                pdf_pages=objects.pdfplumber.pages,
                target_dir=visual_output_dir,
                name_prefix='libpdf_',
                draw_elements=draw_elements,
                render_elements=rendered_elements,
            )
        LOG.info('Visual debug finished successfully.')


def render_pages(
    pdf_pages: List,
    target_dir: str,
    name_prefix: str,
    draw_elements: Dict[int, List[Dict[str, Any]]],
    render_elements: List[str],
):
    """
    Render PDF pages as images containing bounding box of certain elements.

    :param pdf_pages: A list of pdfplumber pages
    :param target_dir: output directory for images
    :param name_prefix: file name prefix, will be appended with <page_numer>.png
    :param draw_elements:   The elements to draw. Key is the page number, the value a dictionary containing the
                            element and the bounding box coordinates. Example::

                                {
                                    2: {
                                        'element': Chapter(),
                                        'x0': 10,
                                        'y0': 10,
                                        'x1': 20,
                                        'y1': 20,
                                    },
                                    3: {...}
                                }

    :param render_elements: list of elements to render, options are chapter, paragraph, table, figure
    :return: None
    """
    render_elements_joined = ', '.join(render_elements)
    LOG.info('Saving annotated images for %s ...', render_elements_joined)

    for page in tqdm(
        pdf_pages,
        desc=f'### Saving {render_elements_joined}',
        unit='pages',
        bar_format=bar_format_lvl1(),
        leave=False,
    ):
        page_no = page.page_number

        if logging_needed(page_no - 1, len(pdf_pages)):
            LOG.info(
                'Saving annotated images for %s page %s of %s',
                render_elements_joined,
                page_no,
                len(pdf_pages),
            )

        if page_no not in draw_elements:
            continue

        draw_elements_page = draw_elements[page_no]

        # filter for elements that shall get rendered
        target_draw_elements = []
        for draw_element in draw_elements_page:
            element_type = type(draw_element['element'])
            if element_type not in MAP_TYPES:
                continue
            str_type = MAP_TYPES[type(draw_element['element'])]
            if str_type in render_elements:
                target_draw_elements.append(draw_element)

        # draw rectangles and save
        # paint bboxes on pdfplumber page and save output
        image = page.to_image(resolution=150)
        for target_draw_element in target_draw_elements:
            bbox = to_pdfplumber_bbox(
                target_draw_element['x0'],
                target_draw_element['y0'],
                target_draw_element['x1'],
                target_draw_element['y1'],
                page.height,
            )
            image.draw_rect(
                bbox,
                fill=VIS_DBG_MAP_ELEMENTS_COLOR[MAP_TYPES[type(target_draw_element['element'])]],
                stroke_width=2,
            )

        image.save(os.path.join(target_dir, name_prefix + f'{page_no}.png'))


def visual_debug_pdfminer(pdf_path, vd_pdfminer_output):
    """Visual debug pdfminer."""
    logging.basicConfig(format='[%(levelname)5s] %(message)s', level=logging.DEBUG)

    LOG.info('Starting layout extraction using only pdfminer')

    logging.getLogger('pdfminer').level = logging.WARNING
    logging.getLogger('PIL').level = logging.WARNING

    page_containers = extract_layout(pdf_path)
    draw_elements = {}
    for page_no, page_container in page_containers.items():
        for lt_element in page_container['elements']:
            draw_element = {
                'element': lt_element,
                'x0': lt_element.x0,
                'y0': lt_element.y0,
                'x1': lt_element.x1,
                'y1': lt_element.y1,
            }
            if page_no not in draw_elements:
                draw_elements[page_no] = [draw_element]
            else:
                draw_elements[page_no].append(draw_element)

    with pdfplumber.open(pdf_path) as pdf:
        pages_list = pdf.pages
    Path(vd_pdfminer_output).mkdir(parents=True, exist_ok=True)
    render_pages(
        pdf_pages=pages_list,
        target_dir=vd_pdfminer_output,
        name_prefix='pdfminer_',
        draw_elements=draw_elements,
        render_elements=RENDER_ELEMENTS,
    )
    LOG.info('Finished successfully')


def extract_layout(path_pdf, idx_single_page=None):
    """Use pdfminer.six to extract LTContainer layout boxes."""
    LOG.info('Extracting layout ...')
    file_pointer = open(path_pdf, 'rb')

    # init pdfminer elements
    parser = PDFParser(file_pointer)
    doc = PDFDocument(parser)
    rsrcmgr = PDFResourceManager()
    laparams = LAParams(char_margin=6, line_margin=0.4)
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pages = PDFPage.create_pages(doc)

    page_containers = {}  # return dictionary

    page_count = doc.catalog['Pages'].resolve()['Count']
    for idx_page, page in enumerate(pages):
        if logging_needed(idx_page, page_count):
            LOG.debug('Extracting layout page %s of %s', idx_page + 1, page_count)
        if idx_single_page is not None and idx_single_page != idx_page:
            continue

        # pdfminer layout analysis
        interpreter.process_page(page)
        lt_page: LTPage = device.get_result()

        page_containers[idx_page + 1] = {'page': page, 'elements': list(lt_page)}

    LOG.info('Finished layout extraction')
    container_count = 0
    for page_container in page_containers.values():
        container_count += len(page_container['elements'])
    LOG.info('Extracted %s containers from %s pages', container_count, page_count)
    return page_containers
