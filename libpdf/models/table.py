"""Definition for PDF tables."""
from operator import attrgetter
from typing import List

from libpdf.models.element import Element
from libpdf.models.link import Link
from libpdf.models.model_base import ModelBase
from libpdf.models.position import Position

from pdfminer.layout import LTTextLineHorizontal


class Table(Element):
    """
    PDF table data.

    :ivar idx: the number of the instance in the current scope, 1-based
    :vartype idx: int
    :ivar cells: a list of Cell instances that are part of the table
    :vartype cells: List[Cell]
    :ivar caption: the caption of the figure (text over/under the table describing it)
    :vartype caption: str
    :ivar position: a Position instance determining the location of the table
    :vartype position: Position
    """

    def __init__(self, idx: int, cells: List['Cell'], position: 'Position', caption=None):
        """Initialize the instance."""
        super().__init__(position=position)
        self.idx = idx
        self.cells = cells
        self.caption = caption
        self.set_cells_backref()

    @property
    def id_(self):
        """
        Return the identifier to address the Table.

        The identifier follows the pattern ``table.<idx>``.
        idx the 1-based number of the Table in the current scope (root, chapter, sub-chapters, page).

        It is used as a link target if a PDF link-annotation points to the Element.

        According to PDF model the parameter should be called ``id`` but the name is reserved in Python, so ``id_``
        is used.

        :type: str
        """
        return f'table.{self.idx}'

    def set_cells_backref(self):
        """Set b_table back reference on all cells."""
        for cell in self.cells:
            cell.b_table = self

    @property
    def rows(self):
        """
        Return a list of rows in the table where each contains a list of columns.

        :type: List[List[Cell]]
        """
        rows = []
        max_row = max(self.cells, key=attrgetter('row')).row  # get highest row number
        for row_nr in range(1, max_row + 1):
            columns_in_row = [cell for cell in self.cells if cell.row == row_nr]
            columns_in_row.sort(key=attrgetter('col'))
            rows.append(columns_in_row)
        return rows

    @property
    def columns(self):
        """
        Return a list of columns in the table where each contains a list of rows.

        :type: List[List[Cell]]
        """
        columns = []
        max_columns = max(self.cells, key=attrgetter('col')).col  # get highest column number
        for col_nr in range(1, max_columns + 1):
            rows_in_column = [cell for cell in self.cells if cell.col == col_nr]
            rows_in_column.sort(key=attrgetter('row'))
            columns.append(rows_in_column)
        return columns

    @property
    def rows_count(self):
        """
        Return the number of rows in the table.

        :type: int
        """
        return len(self.rows)

    @property
    def columns_count(self):
        """
        Return the number of columns in the table.

        :type: int
        """
        return len(self.columns)


class Cell(ModelBase):
    """
    PDF table cell data.

    :ivar row: the row number of the cell, 1-based
    :vartype row: int
    :ivar col: the column number of the cell, 1-based
    :vartype col: int
    :ivar text: the text content of the cell
    :vartype text: str
    :ivar lt_textbox: the lt_textbox of the cell, as extracted from pdfminer
    :vartype lt_textbox: LTTextBoxHorizontal
    :ivar position: a Position instance determining the location of the cell
    :vartype position: Position
    :ivar b_table: a Table instance that contains the cell
    :vartype b_table: Table
    :ivar links: list of links in the cell text
    :vartype links: List[Link]
    """

    def __init__(
        self,
        row: int,
        col: int,
        text: str,
        lt_textbox: LTTextLineHorizontal,
        position: Position,
        links: List[Link],
        table: Table = None,
    ):
        """Initialize the instance."""
        self.row = row
        self.col = col
        self.position = position
        self.b_table = table
        self.text = text
        self.lt_textbox = lt_textbox
        self.links = links
        self.set_backref()
        if self.links:
            self.set_links_backref()

    def set_backref(self):
        """Set b_cell property on self.positions members."""
        if self.position is not None:
            self.position.b_cell = self

    def set_links_backref(self):
        """Set b_source back reference on all links."""
        for link in self.links:
            link.b_source = self

    def __repr__(self):
        """Identify cells by row and column."""
        return f'Cell({self.row}, {self.col}) {self.text}'
