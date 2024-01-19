"""Definition for PDF file meta data."""
from datetime import datetime
from typing import TYPE_CHECKING

from libpdf.models.model_base import ModelBase

# avoid import cycles for back reference type hinting
# https://mypy.readthedocs.io/en/latest/common_issues.html#import-cycles
if TYPE_CHECKING:
    # F401 imported but unused - it's needed for type hinting
    from libpdf.models.file import File  # pylint: disable=cyclic-import


class FileMeta(ModelBase):
    """
    PDF file meta data.

    :ivar author: PDF author meta data field
    :vartype author: str
    :ivar title: PDF title meta data field
    :vartype title: str
    :ivar subject: PDF subject meta data field
    :vartype subject: str
    :ivar creator: PDF creator meta data field
    :vartype creator: str
    :ivar producer: PDF producer meta data field
    :vartype producer: str
    :ivar keywords: PDF keywords meta data field
    :vartype keywords: str
    :ivar creation_date: PDF creation date given as datetime instance
    :vartype creation_date: datetime
    :ivar modified_date: PDF modified date given as datetime instance
    :vartype modified_date: datetime
    :ivar trapped: PDF printing trap flag (https://en.wikipedia.org/wiki/Trap_%28printing%29)
    :vartype trapped: bool
    :ivar b_file: back reference to a File instance
    :vartype b_file: File
    """

    def __init__(  # pylint: disable=too-many-arguments  # it's a data class
        self,
        author: str = None,
        title: str = None,
        subject: str = None,
        creator: str = None,
        producer: str = None,
        keywords: str = None,
        creation_date: datetime = None,
        modified_date: datetime = None,
        trapped: bool = None,
        file: "File" = None,
    ):
        """Initialize the instance."""
        self.author = author
        self.title = title
        self.subject = subject
        self.creator = creator
        self.producer = producer
        self.keywords = keywords
        self.creation_date = creation_date
        self.modified_date = modified_date
        self.trapped = trapped
        self.b_file = file
