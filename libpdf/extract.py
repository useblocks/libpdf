"""Core routines for PDF extraction."""
import itertools
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from libpdf import parameters
from libpdf import process as pro
from libpdf.apiobjects import ApiObjects
from libpdf.catalog import catalog, extract_catalog
from libpdf.exceptions import LibpdfException
from libpdf.log import logging_needed
from libpdf.models.figure import Figure
from libpdf.models.file import File
from libpdf.models.file_meta import FileMeta
from libpdf.models.page import Page
from libpdf.models.position import Position
from libpdf.models.root import Root
from libpdf.parameters import (
    FIGURE_MIN_HEIGHT,
    FIGURE_MIN_WIDTH,
    HEADER_OR_FOOTER_CONTINUOUS_PERCENTAGE,
    LA_PARAMS,
    PAGES_MISSING_HEADER_OR_FOOTER_PERCENTAGE,
    UNIQUE_HEADER_OR_FOOTER_ELEMENTS_PERCENTAGE,
)
from libpdf.progress import bar_format_lvl2, tqdm
from libpdf.tables import extract_pdf_table
from libpdf.textbox import extract_linked_chars, extract_paragraphs_chapters
from libpdf.utils import lt_page_crop, lt_to_libpdf_hbox_converter, to_pdfplumber_bbox

from pdfminer.layout import LTText

import pdfplumber

import yaml

LOG = logging.getLogger(__name__)


class FoldedStr(str):
    """Pass the folded string for scalar node."""


def folded_str_representer(dumper, text):
    """Warp function of the representer."""
    return dumper.represent_scalar('tag', text, style='>')


yaml.add_representer(FoldedStr, folded_str_representer)


def extract(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements, too-many-arguments
    pdf_path: str,
    pages: Optional[List[int]],
    smart_page_crop: bool,
    save_figures: bool,
    figure_dir: Optional[str],
    no_annotations: bool,
    no_chapters: bool,
    no_paragraphs: bool,
    no_tables: bool,
    no_figures: bool,
    overall_pbar: tqdm,
) -> ApiObjects:
    """
    Run main PDF extraction logic.

    :param pdf_path: path to the PDF to read
    :param pages: list of pages to extract
    :param smart_page_crop: see description in function core.main()
    :param save_figures: flag triggering the export of figures to the figure_dir
    :param figure_dir: output directory for extracted figures
    :param no_annotations: flag triggering the exclusion of annotations from pdf catalog
    :param no_chapters: flag triggering the exclusion of chapters (flat structure of elements)
    :param no_paragraphs: flag triggering the exclusion of paragraphs (no normal text content)
    :param no_tables: flag triggering the exclusion of tables
    :param no_figures: flag triggering the exclusion of figures
    :param overall_pbar: total progress bar for whole libpdf run
    :return: instance of Objects class
    :raise LibpdfException: PDF contains no pages
    """
    LOG.info('PDF extraction started ...')

    LOG.info('Loading the PDF with pdfminer LTTextBox analysis ...')

    with pdfplumber.open(pdf_path, laparams=LA_PARAMS) as pdf:
        LOG.info('The PDF has %s pages', len(pdf.pages))
        if pages:
            # TODO:
            #  2. checkout if delete pages works before pdfplumber loading pdf, which can probably improve performance
            #  3. page_range extract cover feature header/footer???
            includelist_non_existent = [page for page in pages if page <= 0 or page > len(pdf.pages)]
            if includelist_non_existent:
                LOG.error(
                    'The selected page number(s) [%s] do not exist in the pdf. They will be skipped.',
                    ','.join([str(x) for x in includelist_non_existent]),
                )

            # delete pages from pdfplumber that are not in the extracted_pages list
            includelist_existent = list(set(pages) - set(includelist_non_existent))
            for page in pdf.pages.copy():
                if page.page_number not in includelist_existent:
                    pdf.pages.remove(page)

            if len(pdf.pages) == 0:
                message = 'Page range selection: no pages left in the PDF to analyze.'
                LOG.critical(message)
                raise LibpdfException(message)

        overall_pbar.update(5)
        pdf = delete_page_ann(pdf)
        overall_pbar.update(10)

        # extract file info to instantiate libpdf.models.file.File
        # and libpdf.models.file_meta.FileMeta classes
        file = file_info_extraction(pdf, pdf_path)
        overall_pbar.update(1)

        # get page sizes and numbers
        pages_list = extract_page_metadata(pdf)

        if not pages_list:
            raise LibpdfException('PDF contains no pages')

        overall_pbar.update(1)

        # extract annotations, name destinations and outline
        extract_catalog(pdf, no_annotations)
        overall_pbar.update(10)

        # In figure_dict, figures are sorted by pages and y coordinates.
        # It is the pre-process for the table extraction to see if the table is recognised as the figure
        # In some cases, an element is recognised as a table and a figure at the same time
        if no_figures:
            LOG.info('Excluding figures extraction')
            figure_list = []
        else:
            figure_list = extract_figures(pdf, pages_list, figure_dir)
            # smartly remove figures that are in header and footer
            if smart_page_crop:
                figure_list = smart_page_crop_header_footer(pdf, figure_list)
        overall_pbar.update(30)

        if no_tables:
            LOG.info('Excluding tables extraction')
            table_list = []
        else:
            table_list = extract_pdf_table(pdf, pages_list, figure_list)
        overall_pbar.update(25)

        # smartly remove tables that are in header and footer
        if smart_page_crop:
            table_list = smart_page_crop_header_footer(pdf, table_list)

        paragraph_list, chapter_list = extract_paragraphs_chapters(
            pdf,
            figure_list,
            table_list,
            pages_list,
            no_chapters,
            no_paragraphs,
        )

        # smartly remove paragraphs that are in header and footer
        if smart_page_crop:
            paragraph_list = smart_page_crop_header_footer(pdf, paragraph_list)

        element_list = pro.merge_all_elements(figure_list, table_list, paragraph_list, chapter_list)

        # to check if elements shall be mapped into nested outline structure.
        if catalog['outline'] is not None and not no_chapters:
            element_list = pro.map_elements_outline(element_list, catalog['outline'])

        root = Root(file, pages_list, element_list)

        if catalog['annos']:
            pro.libpdf_target_explorer(paragraph_list, pages_list)
            pro.libpdf_target_explorer(table_list, pages_list)

        overall_pbar.update(10)

        # write out figures to given path
        if save_figures:
            images_to_save(pdf, figure_list)

    # populate ApiObjects
    objects = ApiObjects(
        root=root,
        chapters=chapter_list,
        paragraphs=paragraph_list,
        tables=table_list,
        figures=figure_list,
        pdfplumber=pdf,
        pdfminer=pdf.doc,
    )

    return objects


def smart_page_crop_header_footer(  # pylint: disable=too-many-branches, too-many-locals  # noqa: C901  # too-complex
    pdf,
    elements_list,
):
    """
    Remove header and footer elements smartly.

    Check element that inside given parameter of header and footer margin, by default is SMART_PAGE_CROP_REL_MARGINS
    of page height, if this element appears on more than HEADER_FOOTER_OCCURRENCE_PERCENTAGE pages, then consider it
    as potential header or footer element.

    To filter out false positive detected header/footer elements, it needs to check the height change of the potential
    header or footer element, if this element's height continuously change from page to page, the jump up and down
    happens more than HEADER_FOOTER_CONTINUOUS_PERCENTAGE of pages, and also need to check the unique y coordinates,
    real header/footer elements in pdf should have same y coordinates ideally, if unique y coordinates occurs less than
    HEADER_FOOTER_UNIQUE_Y_POSITION_PERCENTAGE pages, then consider it not a header or footer element.
    """
    # restructure elements_list to dict with page based
    elements_page_dict = {}
    for element in elements_list:
        if element.position.page.number not in elements_page_dict:
            elements_page_dict[element.position.page.number] = []
            elements_page_dict[element.position.page.number].append(element)
        else:
            elements_page_dict[element.position.page.number].append(element)

    # smart algorithm to determine which elements shall be removed
    page_height = float(pdf.pages[0].mediabox[3])

    header_elements_list = []
    default_header_bottom = (1 - parameters.SMART_PAGE_CROP_REL_MARGINS['top']) * page_height

    for pot_header_elements in elements_page_dict.values():  # pylint: disable=too-many-nested-blocks
        # potential header element
        for pot_header_element in pot_header_elements:
            page_cnt = 0
            # consider element partially inside potential header bbox
            if pot_header_element.position.y0 >= default_header_bottom:
                for header_elements in elements_page_dict.values():
                    element_cnt = 0
                    for header_element in header_elements:
                        if (
                            abs(pot_header_element.position.y0 - header_element.position.y0) < 1
                            and abs(pot_header_element.position.y1 - header_element.position.y1) < 1
                        ):
                            element_cnt += 1
                    # on one page several header elements may have same y coordination but count only once
                    element_cnt = min(element_cnt, 1)
                    page_cnt = page_cnt + element_cnt
            # occur on more than HEADER_FOOTER_OCCURRENCE_PERCENTAGE pages, considered as header element
            # and remove from list
            if page_cnt >= parameters.HEADER_FOOTER_OCCURRENCE_PERCENTAGE * len(pdf.pages):
                header_elements_list.append(pot_header_element)

    # remove false header elements from potential header elements list
    if header_elements_list:
        real_header_elements_list = check_false_positive_header_footer(pdf, header_elements_list)
    else:
        real_header_elements_list = header_elements_list

    # remove header elements
    elements_list = [element for element in elements_list if element not in real_header_elements_list]

    footer_elements_list = []
    default_footer_top = parameters.SMART_PAGE_CROP_REL_MARGINS['bottom'] * page_height
    for pot_footer_elements in elements_page_dict.values():  # pylint: disable=too-many-nested-blocks
        # potential footer element
        for pot_footer_element in pot_footer_elements:
            page_cnt = 0
            # consider element partially insider potential footer bbox
            if pot_footer_element.position.y1 <= default_footer_top:
                for footer_elements in elements_page_dict.values():
                    element_cnt = 0
                    for footer_element in footer_elements:
                        if (
                            abs(pot_footer_element.position.y0 - footer_element.position.y0) < 1
                            and abs(pot_footer_element.position.y1 - footer_element.position.y1) < 1
                        ):
                            element_cnt += 1
                    # on one page several footer elements may have same y coordination but count only once
                    element_cnt = min(element_cnt, 1)
                    page_cnt = page_cnt + element_cnt
            # occur on more than HEADER_FOOTER_OCCURRENCE_PERCENTAGE pages, considered as footer element
            # and remove from list
            if page_cnt >= parameters.HEADER_FOOTER_OCCURRENCE_PERCENTAGE * len(pdf.pages):
                footer_elements_list.append(pot_footer_element)

    # filter out false footer elements
    if footer_elements_list:
        real_footer_elements_list = check_false_positive_header_footer(pdf, footer_elements_list)
    else:
        real_footer_elements_list = footer_elements_list

    # remove footer elements
    elements_list = [element for element in elements_list if element not in real_footer_elements_list]

    return elements_list


def check_false_positive_header_footer(pdf, elements_list):  # pylint: disable=too-many-branches
    """
    Filter out not real header/footer elements from given potential header/footer elements list.

    A element will be considered as a header/footer element:

        1. same y0 coordination
        2. and continuously appears from page to page

    That's most ideally situation, header/footer element appears on the same location continuously
    from start page to end page.

    We configure two default parameters to cover most of the scenarios for the above mentioned criterion:

        1. continuous boundary: the maximal page breaks we allow for header/footer element
        2. unique same y0 coordination: because some pdf have separate header/footer style across the whole pdf

    Go though the potential header/footer elements list, find the lowest y0 element on each page in the given list,
    check the criterion page break and unique y0 for all the lowest y0 elements through all the pages, if not meet
    the criterion, then remove it from the potential header/footer elements list, then recursively check again.
    """
    elements_page_dict = {}
    for element in elements_list:
        if element.position.page.number not in elements_page_dict:
            elements_page_dict[element.position.page.number] = []
            elements_page_dict[element.position.page.number].append(element)
        else:
            elements_page_dict[element.position.page.number].append(element)

    # search the lowest element height on each page
    element_low_pos_dict = {}
    for page_num, elements in elements_page_dict.items():
        lowest_element_pos = float(f'{elements[0].position.y0:.4f}')  # restrict to 4 digits precision
        for element in elements:
            lowest_element_pos = min(lowest_element_pos, float(f'{element.position.y0:.4f}'))
        element_low_pos_dict[page_num] = lowest_element_pos

    start_page_low_pos = list(element_low_pos_dict)[0]
    end_page_low_pos = list(element_low_pos_dict)[-1]
    page_breaks = end_page_low_pos - start_page_low_pos + 1 - len(element_low_pos_dict)
    # find the lowest y0
    header_low_pos = min(set(element_low_pos_dict.values()))
    # check continuous of potential header/footer element from start page to end page
    if page_breaks / (end_page_low_pos - start_page_low_pos + 1) <= PAGES_MISSING_HEADER_OR_FOOTER_PERCENTAGE:
        # check unique low_pos
        if len(set(element_low_pos_dict.values())) != 1:
            # a list of page numbers to check the element's continuous
            continuous_page_list = []
            for page, low_pos_element in element_low_pos_dict.items():
                if low_pos_element == header_low_pos:
                    continuous_page_list.append(page)
            # check header/footer continuous
            sorted_continuous_page_list = sorted(continuous_page_list)
            continuous_list_length = sorted_continuous_page_list[-1] - sorted_continuous_page_list[0] + 1
            # TODO: need to improve the parameter UNIQUE_HEADER_OR_FOOTER_ELEMENTS_PERCENTAGE to solve
            #  partially continuous header or footer elements
            if len(
                sorted_continuous_page_list,
            ) < continuous_list_length * HEADER_OR_FOOTER_CONTINUOUS_PERCENTAGE and len(
                set(element_low_pos_dict.values()),
            ) > max(
                1,
                UNIQUE_HEADER_OR_FOOTER_ELEMENTS_PERCENTAGE * len(pdf.pages),
            ):
                for idx, element in enumerate(elements_list):
                    if float(f'{element.position.y0:.4f}') == header_low_pos:
                        del elements_list[idx]
                # recursively check again, to find the next min_low_pos, which will determine the header/footer boundary
                if elements_list:
                    return check_false_positive_header_footer(pdf, elements_list)
        else:
            if len(elements_list) == 1:
                elements_list.pop()
    else:
        for idx, element in enumerate(elements_list):
            if float(f'{element.position.y0:.4f}') == header_low_pos:
                del elements_list[idx]
        # recursively check again, to find the next min_low_pos, which will determine the header/footer boundary
        if elements_list:
            return check_false_positive_header_footer(pdf, elements_list)

    return elements_list


def delete_page_ann(pdf):
    """
    Delete useless ann in pages.

    After running the layout analysis by passing the laparams to pdfplumber, the objects in
    pdf.pages[].objects['anno'] contain strange items with no coordinates x0 etc. which leads to exceptions
    later.
    See here: https://github.com/jsvine/pdfplumber/issues/1#issuecomment-606225926
    Below is a dirty hack that deletes these keys which also affects pdf.objects['anno'] as it is sourced from
    the page.objects. The deletion of the anno object seems to do no harm, at least the test cases are ok.

    :param pdf:
    :return:
    """
    LOG.info('Deleting strange anno objects created by layout analysis ...')
    for idx_page, page in enumerate(
        tqdm(pdf.pages, desc='###### Deleting anno objects', unit='pages', bar_format=bar_format_lvl2()),
    ):
        if logging_needed(idx_page, len(pdf.pages)):
            LOG.debug(
                'Deleting strange anno objects created by layout analysis page %s of %s',
                idx_page + 1,
                len(pdf.pages),
            )
        # filter out the strange items
        if 'anno' in page.objects:
            page.objects['anno'] = [
                item
                for item in page.objects['anno']
                if not (item['object_type'] == 'anno' and item['text'] in [' ', '\n'])
            ]
            if not page.objects['anno']:
                #  remove the whole key if it's empty after above operation
                del page.objects['anno']

    return pdf


def file_info_extraction(pdf, pdf_path):
    """
    Extract file info to instantiate File class and FileMeta class.

    Instantiate :class:`~libpdf.models.file.File` and class:`~libpdf.models.file_meta.FileMeta` classes by extracting
    file and file meta data information like file id, file name, pdf path, Author, Title, creation_date.

    :param pdf: instance of pdfplumber.pdf.PDF class
    :param pdf_path: path to the PDF to read
    :return: File object containing file and file meta information
    """
    LOG.info('Extracting file information ...')
    file_name = os.path.basename(pdf_path)

    # date format string example D:20110120163651-05'00'
    # zulu timezone Z0000 will be converted to +0000
    def _time_preprocess(date_str):  # converts to 20110120163651-0500
        return date_str.replace('D:', '').replace("'", '').replace('Z', '+')

    def _get_datetime_format(date: str):
        """
        Guess the datetime format string based on the existence of +- in the string which stands for the timezone.

        The returned format string is valid after pre-processing, see _time_preprocess().
        """
        if '+' in date or '-' in date:
            return '%Y%m%d%H%M%S%z'  # with timezone
        return '%Y%m%d%H%M%S'  # without timezone

    file_meta_params = {}
    if 'Author' in pdf.metadata:
        file_meta_params.update({'author': pdf.metadata['Author']})
    if 'Title' in pdf.metadata:
        file_meta_params.update({'title': pdf.metadata['Title']})
    if 'Subject' in pdf.metadata:
        file_meta_params.update({'subject': pdf.metadata['Subject']})
    if 'Creator' in pdf.metadata:
        file_meta_params.update({'creator': pdf.metadata['Creator']})
    if 'Producer' in pdf.metadata:
        file_meta_params.update({'producer': pdf.metadata['Producer']})
    if 'Keywords' in pdf.metadata:
        file_meta_params.update({'keywords': pdf.metadata['Keywords']})
    if 'CreationDate' in pdf.metadata:
        preprocessed_date = _time_preprocess(pdf.metadata['CreationDate'])
        time_format = _get_datetime_format(preprocessed_date)
        file_meta_params.update({'creation_date': datetime.strptime(preprocessed_date, time_format)})
    if 'ModDate' in pdf.metadata:
        preprocessed_date = _time_preprocess(pdf.metadata['ModDate'])
        time_format = _get_datetime_format(preprocessed_date)
        file_meta_params.update({'modified_date': datetime.strptime(preprocessed_date, time_format)})
    if 'Trapped' in pdf.metadata:
        file_meta_params.update({'trapped': pdf.metadata['Trapped']})

    file_meta_data = FileMeta(**file_meta_params)

    file_obj = File(
        file_name,
        pdf_path,
        len(pdf.pages),
        parameters.PAGE_CROP_MARGINS['top'],
        parameters.PAGE_CROP_MARGINS['bottom'],
        parameters.PAGE_CROP_MARGINS['left'],
        parameters.PAGE_CROP_MARGINS['right'],
        file_meta_data,
    )

    file_meta_data.b_file = file_obj

    return file_obj


def extract_page_metadata(pdf):
    """
    Extract page metadata to instantiate Page class.

    Extract page metadata from pdfplumber.pdf.PDF.pages and
    instantiate pdfplumber.page.Page class for each page in given pdf.

    :param pdf: instance of pdfplumber.pdf.PDF class
    :return: A list of Page objects
    """
    LOG.info('Extracting page metadata ...')
    page_list = []

    for idx_page, page in enumerate(
        tqdm(pdf.pages, desc='###### Extracting metadata', unit='pages', bar_format=bar_format_lvl2()),
    ):
        if logging_needed(idx_page, len(pdf.pages)):
            LOG.debug('Extracting metadata page %s of %s', idx_page + 1, len(pdf.pages))
        page_obj = Page(page.page_number, float(page.width), float(page.height))
        page_list.append(page_obj)

    return page_list


def extract_figures(
    pdf,
    pages_list,
    figure_dir,
) -> List[
    Figure
]:  # pylint: disable=too-many-nested-blocks, too-many-branches  # local algorithm, easier to read when not split up
    """Extract figures in PDF."""
    LOG.info('Extracting figures ...')
    figure_list = []

    for idx_page, page in enumerate(  # pylint: disable=too-many-nested-blocks
        tqdm(pdf.pages, desc='###### Extracting figures', unit='pages', bar_format=bar_format_lvl2()),
    ):
        if logging_needed(idx_page, len(pdf.pages)):
            LOG.debug('Extracting figures page %s of %s', idx_page + 1, len(pdf.pages))
        page_crop = pro.remove_page_header_footer(page)
        lt_page = page._layout  # pylint: disable=protected-access  # easiest way to obtain LTPage

        # check and filter figures
        figures = check_and_filter_figures(page_crop.figures)

        if len(figures) != 0:
            for idx_figure, figure in enumerate(figures):
                fig_pos = Position(
                    float(figure['x0']),
                    float(figure['y0']),
                    float(figure['x1']),
                    float(figure['y1']),
                    pages_list[idx_page],
                )
                bbox = (fig_pos.x0, fig_pos.y0, fig_pos.x1, fig_pos.y1)

                lt_textboxes = lt_page_crop(
                    bbox,
                    lt_page._objs,  # pylint: disable=protected-access # access needed
                    LTText,
                    contain_completely=True,
                )

                textboxes = []
                links = []
                for lt_textbox in lt_textboxes:
                    if catalog['annos']:
                        links.extend(extract_linked_chars(lt_textbox, lt_page.pageid))
                    bbox = (lt_textbox.x0, lt_textbox.y0, lt_textbox.x1, lt_textbox.y1)

                    hbox = lt_to_libpdf_hbox_converter(lt_textbox)

                    textboxes.append(hbox)

                image_name = f'page_{page.page_number}_figure.{idx_figure + 1}.png'

                # create figures directory if not exist
                Path(figure_dir).mkdir(parents=True, exist_ok=True)

                image_path = os.path.abspath(os.path.join(figure_dir, image_name))

                figure = Figure(idx_figure + 1, image_path, fig_pos, links, textboxes, 'None')
                figure_list.append(figure)

    return figure_list


def images_to_save(pdf, figure_list):
    """Save images to given path."""
    for fig in figure_list:
        for pdf_page in pdf.pages:
            if pdf_page.page_number == fig.position.page.number:
                page = pdf_page

        page_crop = pro.remove_page_header_footer(page)

        bbox = to_pdfplumber_bbox(fig.position.x0, fig.position.y0, fig.position.x1, fig.position.y1, page.height)
        crop_page_figure = page_crop.within_bbox(bbox)
        image_path = fig.rel_path

        image = crop_page_figure.to_image(resolution=300)
        image.save(image_path, format='png')


def check_and_filter_figures(figures_list):  # pylint: disable=too-many-branches
    """
    Check and filter unneeded figures from given figures list.

    Remove figures that are too small for human, or figures partially outside page,
    or completely inside or overlapped with other figures.

    Examples::

        Remove figure's part, which is          Remove small figure, which inside
        outside the page                        big figure
        +-----page------------------------+     +----page------------------------+
        |                                 |     |        +--------figure-----+   |
        |                                 |     |        |                   |   |
      +--figure---+                       |     |        |   +---figure----+ |   |
      |           |                       |     |        |   |             | |   |
      |           |                       |     |        |   |             | |   |
      |           |                       |     |        |   |             | |   |
      +-----------+                       |     |        |   +-------------+ |   |
        |                                 |     |        +-------------------+   |
        +---------------------------------+     +--------------------------------+

        Remove too small figure, which not      Remove partially overlapped figure,
        human readable                          which is smaller than the other
        +-----page------------------------+     +-----page------------------------+
        |                                 |     |                                 |
        |                                 |     |    +-----figure---+             |
        |  +--+                           |     |  +-|--figure-+    |             |
        |  |  |                           |     |  | |         |    |             |
        |  +--+                           |     |  | |         |    |             |
        |                                 |     |  | |         |    |             |
        |                                 |     |  | +---------|----+             |
        |                                 |     |  +-----------+                  |
        |                                 |     |                                 |
        +---------------------------------+     +---------------------------------+

    :param figures_list: A list of extracted figures from pdfplumber
    :return: A list of filtered figures
    """
    filtered_figures = []
    for figure in figures_list:
        # check if figure really exist and figure's size if it's human readable
        if figure['height'] > FIGURE_MIN_HEIGHT and figure['width'] > FIGURE_MIN_WIDTH:
            filtered_figures.append(figure)

    for figure in filtered_figures:
        # if figure exceed the boundary of the page, then only keep the part of figure that inside this page
        if not (figure['x0'] >= 0 and figure['y0'] >= 0 and figure['x1'] >= 0 and figure['y1'] >= 0):
            if figure['x0'] < 0:
                figure['x0'] = 0
            if figure['y0'] < 0:
                figure['y0'] = 0
            if figure['x1'] < 0:
                figure['x1'] = 0
            if figure['y1'] < 0:
                figure['y1'] = 0

    # check if figures completely inside another figures and remove small figures
    for fig0, fig1 in itertools.combinations(filtered_figures, 2):
        if (
            fig0['x0'] <= fig1['x0']
            and fig0['y0'] <= fig1['y0']
            and fig0['x1'] >= fig1['x1']
            and fig0['y1'] >= fig1['y1']
        ):
            if fig1 in filtered_figures:
                filtered_figures.remove(fig1)

    # check if figures partially overlap
    for fig0, fig1 in itertools.combinations(filtered_figures, 2):
        # check partially overlap
        if not (
            fig0['x0'] > fig1['x1'] or fig0['x1'] < fig1['x0'] or fig0['y0'] > fig1['y1'] or fig0['y1'] < fig1['y0']
        ):
            if not (
                fig0['x0'] <= fig1['x0']
                and fig0['y0'] <= fig1['y0']
                and fig0['x1'] >= fig1['x1']
                and fig0['y1'] >= fig1['y1']
            ):
                # compare the size of two figures, keep the bigger figure
                if fig0['width'] * fig0['height'] <= fig1['width'] * fig1['height']:
                    if fig0 in filtered_figures:
                        filtered_figures.remove(fig0)
                else:
                    if fig1 in filtered_figures:
                        filtered_figures.remove(fig1)

    return filtered_figures
