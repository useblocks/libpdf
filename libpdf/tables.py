"""
Extracts tables cells and texts inside.

Coordinate system (positions) of tables is defined below:

(x0,y1)-------------(x1,y1)
|                        |
|                        |
|                        |
|                        |
|                        |
(x0,y0)-------------(x1,y0)

pdfminer   sees y0 and y1 from the bottom of the page
pdfplumber sees y0 and y1 from the top of the page

pdfminer's layout is used.
"""

import logging
from decimal import Decimal
from typing import List, Union

from pdfminer.layout import LTPage, LTTextBoxHorizontal

from libpdf import textbox, utils
from libpdf.catalog import catalog
from libpdf.log import logging_needed
from libpdf.models.figure import Figure
from libpdf.models.page import Page
from libpdf.models.position import Position
from libpdf.models.table import Cell, Table
from libpdf.parameters import LA_PARAMS
from libpdf.progress import bar_format_lvl2, tqdm
from libpdf.utils import from_pdfplumber_bbox, lt_to_libpdf_hbox_converter

LOG = logging.getLogger(__name__)


class FoldedStr(str):
    """Pass the folded string for scalar node."""


def folded_str_representer(dumper, text):
    """Warp function of the representer."""
    return dumper.represent_scalar("tag", text, style=">")


def extract_pdf_table(pdf, pages_list: List[Page], figure_list: List[Figure]):
    """
    Extract the table in PDF.

    Table extraction is done by pdfplumber and LTPage are fetched from pdf.page._layout. LTPage is needed for
    text extraction in cells.

    :param pdf: pdf object from pdfplumber. It contains LTPage from pdfminer
    :param pages_list: a list of libpdf Page objects, which will be referred by the tables extracted
    :param figure_list: a list of libpdf Figure objects, used to see if tables and figures are overlapped
    :return: a list of tables
    """
    LOG.info("Extracting tables ...")
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "explicit_vertical_lines": [],
        "explicit_horizontal_lines": [],
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 3,
        "min_words_vertical": 3,
        "min_words_horizontal": 1,
        "text_keep_blank_chars": False,
        "text_tolerance": 3,
        "text_x_tolerance": 2,
        "text_y_tolerance": 2,
        "intersection_tolerance": 3,
    }

    table_dict = {"page": {}}
    table_list = []
    table_id = 1
    for idx_page, page in enumerate(
        tqdm(
            pdf.pages,
            desc="###### Extracting tables",
            unit="pages",
            bar_format=bar_format_lvl2(),
        ),
    ):
        if logging_needed(idx_page, len(pdf.pages)):
            LOG.debug("Extracting tables page %s of %s", idx_page + 1, len(pdf.pages))
        if len(page.find_tables(table_settings)) != 0:
            table_dict["page"].update({idx_page + 1: []})
            tables = page.find_tables(table_settings)
            lt_page = page._layout  # pylint: disable=protected-access  # easiest way to obtain LTPage
            for table in tables:
                # bbox in tables use pdfplumber bbox coordination (x0, top, y0, bottom), hence, need to
                # convert pdfplumber table coordination (x0, top, x1, bottom) to pdfminer standard (x0, y0, x1, y1)
                table_pos_bbox = from_pdfplumber_bbox(
                    table.bbox[0],
                    table.bbox[1],
                    table.bbox[2],
                    table.bbox[3],
                    page.height,
                )

                table_pos = Position(
                    table_pos_bbox[0],
                    table_pos_bbox[1],
                    table_pos_bbox[2],
                    table_pos_bbox[3],
                    pages_list[idx_page],
                )

                if _table_figure_check(table_pos, figure_list) is True:
                    table_dict["page"][idx_page + 1].append(
                        {
                            "id": "table." + str(table_id),
                            "type": "table",
                            "positions": table_pos,
                            # 'text': table_temp.extract(2, 2),
                            "cell": [],
                        },
                    )

                    cells = extract_cells(
                        lt_page,
                        table.rows,
                        table_dict["page"][idx_page + 1][
                            len(table_dict["page"][idx_page + 1]) - 1
                        ]["cell"],
                        pages_list[idx_page],
                    )

                    table = Table(idx=table_id, cells=cells, position=table_pos)
                    table_list.append(table)

                    table_id += 1

            if len(table_dict["page"][idx_page + 1]) == 0:  # no table is added
                del table_dict["page"][idx_page + 1]

    return table_list


def extract_cells(lt_page: LTPage, rows: List, list_cell: List[Cell], page: Page):
    """
    Extract cells in the table.

    :param lt_page: LTPage instance
    :param rows: a list of rows in the current table
    :param list_cell: a empty list of cells for each table will be updated
    :param pages_list: a list of pages
    :return: list of Cell objects
    """
    cell_obj_list = []
    for idx_row, row in enumerate(rows):
        for idx_cell, row_cell in enumerate(row.cells):
            if row_cell is not None:  # for merged cells
                pos_cell_bbox = from_pdfplumber_bbox(
                    row_cell[0],
                    row_cell[1],
                    row_cell[2],
                    row_cell[3],
                    lt_page.height,
                )
                pos_cell = Position(
                    pos_cell_bbox[0],
                    pos_cell_bbox[1],
                    pos_cell_bbox[2],
                    pos_cell_bbox[3],
                    page,
                )
                # extract cell text
                lt_textbox = cell_lttextbox_extraction(pos_cell, lt_page)
                links = []
                text_cell = ""
                if lt_textbox:
                    text_cell = lt_textbox.get_text()
                    if catalog["annos"]:
                        links = textbox.extract_linked_chars(lt_textbox, lt_page.pageid)

                    hbox = lt_to_libpdf_hbox_converter([lt_textbox])
                else:
                    hbox = None

                cell = {
                    "row": idx_row + 1,
                    "col": idx_cell + 1,
                    "positions": pos_cell_bbox,
                    "text": FoldedStr(text_cell),
                    "links": links,
                }

                list_cell.append(cell)

                cell_obj = Cell(
                    idx_row + 1, idx_cell + 1, pos_cell, links, textbox=hbox
                )
                cell_obj_list.append(cell_obj)

    return cell_obj_list


def _table_figure_check(positions: Position, figure_list: List[Figure]):
    """
    Check if the table is recognized as the figure in the same page.

    In some cases, a table may be recognised as a table and a figure at the same time. It happened before,
    but I forgot in which pdf I found this occurred.

    :param positions: The position of a table
    :param figure_list: A list of figure
    :return: True means only table is recognised.
    """
    if len(figure_list) > 0:
        filter_list_figure = list(
            filter(lambda x: x.position.page.number == positions.page, figure_list)
        )
        if len(filter_list_figure) > 0:
            margin_offset = 5
            for figure in filter_list_figure:
                # TODO: don't get this, maybe ascii art will be helpful, why margin_offset = 5???
                if (
                    (figure.position.x0 - margin_offset) < positions.x0
                    and (figure.position.y0 + margin_offset) > positions.y0
                    and (figure.position.x1 + margin_offset) > positions.x1
                    and (figure.position.y1 - margin_offset) < positions.y1
                ):  # check if the position of the table is in the figure
                    return False

    return True


def cell_lttextbox_extraction(
    position: Position, lt_page: LTPage
) -> Union[LTTextBoxHorizontal, None]:
    """
    Extract the lttextbox in the cell.

    :param position: a bounding box describing the cell's position
    :param lt_page: LTPage instance
    :return:
    """
    # TODO: offset explanation
    offset = 5

    cell_bbox = [
        position.x0 - offset,
        position.y0 - offset,
        position.x1 + offset,
        position.y1 + offset,
    ]
    lt_textbox = utils.lt_textbox_crop(
        cell_bbox,
        lt_page._objs,  # pylint: disable=protected-access  # not publicly available
        word_margin=LA_PARAMS["word_margin"],
        y_tolerance=LA_PARAMS["line_overlap"],
    )

    return lt_textbox
