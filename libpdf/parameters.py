"""Central place for fixed and changeable application parameters."""

##################
# FIXED PARAMETERS
##################

# The texts inside tables shall not be LTTextBoxes. Instead, they shall be extracted by the page crop on the cell.
# In this case, all of the LTTextBoxes inside tables shall be either ignored or removed. However, Some LTTextboxes
# which are supposed to be inside a table may exceed the boundary of that table. To tackle it, the TABLE_MARGIN is
# introduced to expand the coverages of tables to make sure the LTTextboxes inside the tables can all be found.
# The value here is defined by experiences. It can differ in different kinds of PDF layouts. Machine learning may be
# a good solution to decide the value in the further.

# *----------table--------*
# |           |           |      The text may be in the cell of the table but its boundary box
# |           |  +----------+    is out of the table somehow. TABLE_MARGIN is used to make sure
# |           |  | LTtext | |    this text is considered as the part inside the table cell.
# |           |  +----------+
# |----cell---|----cell---|
# |           |           |
# |           |           |
# |           |           |
# *-----------------------*
#
# Given in points (72 points = 1 inch = 25.4 mm)
TABLE_MARGIN = 8
#
# To find out if a certain LTTextBox is actually the title of a chapter in the outline, lippdf
# checks if the top-left coordinate (x,y) of a LTTextBox overlap on that of a title in outline catalog.
# However, the coordinates of LTTextBox and outline catalog are not totally the same, so a tolerance
# value is introduced. This value is based on experiences
#
#   -----------------------
#   |          |    ^     |
#   | <--t-->  |    |     |         +  <-- the top-left coordinate of the potential title in a LTTextbox
#   |          |    t     |
#   |     +    |    v     |         * <-- the top-left coordinate of a chapter title in outline catalog
#   |----------*----------|
#   |          |    ^     |         t is HEADLINE_TOLERANCE
#   |          |    |     |
#   | <--t-->  |    t     |         as long as + is in the boundary where the * is the center and
#   |          |    v     |         t is the radius of the rectangle, + will be condiered as the title of the chapter
#   -----------------------
#
# Given in points (72 points = 1 inch = 25.4 mm)
HEADLINE_TOLERANCE = 20

# If a chapter in a certain page is not rendered from a matched textbox, a "simulated chapter" will be rendered from
# the chapter in outline catalog. In this case, only one point coordinate (x,y) is available in outline catalog.
# However, a chapter need a rectangle coordinate (x0, y0, x1, y1) to be rendered. Therefore, an extended distance is
# introduced for the chapters rendered from outline catalog. The logic is as follows::
#
#     (x, y - CHAPTER_RECTANGLE_EXTEND, x + CHAPTER_RECTANGLE_EXTEND, y)
#     *-page------------------------*
#     |                             |
#     |                             |
#     |                             |
#     |        x,y--------+         |
#     |<--x0-->|          |   ^     |
#     |        |          |   |     |
#     |<-------|< extend >|   |     |
#     |        +----------+   |     |
#     |            ^          |     |
#     |           y0         y1     |
#     |            v          v     |
#     *-----------------------------*
#
# Given in points (72 points = 1 inch = 25.4 mm)
CHAPTER_RECTANGLE_EXTEND = 20

# To extract the textbox considered as the chapter, the tolerance needs to be applied. It is to make sure the
# extracted region is bigger than the textbox itself. If the extracted region is exactly equal to the position of the
# textbox, the function "utils.text_crop()" won't extract the textbox.
CHAPTER_TEXTBOX_TOLERANCE = 1

# difflib SequenceMatcher is used to compare PDF outline text with textbox
# content created by pdfminer layout analysis. The textbox is only selected if
# the text similarity is higher than the following value.
MIN_OUTLINE_TITLE_TEXTBOX_SIMILARITY = 0.6

# Annotation rectangle may not completely cover the characters which are supposed to be annotated. In this case,
# the statically vertical and horizontal offset is introduced to make sure the annotated characters are extracted
# correctly. The annotation bbox will be increased in all directions by below parameter values.
# Given in points (72 points = 1 inch = 25.4 mm)
ANNO_X_TOLERANCE = 3
ANNO_Y_TOLERANCE = 3

# In the conversion of linked_chars, the algorithm tries to find the corresponding element which completely covers
# the target link pointing to a (x ,y) position on a certain page. The target link always presumably directs to
# the top-left of an elements. However, the target link may not even be covered or closed to
# the corresponding element. In this case, an element is considered as the base and
# the vertical and horizontal tolerances are introduced to upwards and leftwards search for the link target.
#
#     (x0 - TARGET_COOR_TOLERANCE, y0, x1, y1 + TARGET_COOR_TOLERANCE)
#     *-page----------------------------------*
#     |                                       |
#     |<-------x1------------------->         |
#     |                                       |
#     |    +-------------------------+        |
#     |    |  (x,y)       ^          |        |
#     |    |    *         |tolerance |        |
#     |    |              v          |        |
#     |    |             +-----------+        |
#     |    |             |           |   ^    |
#     |    |             |    an     |   |    |
#     |    |             |  element  |   |    |
#     |    |< tolerance >|           |   |    |
#     |    +-------------+-----------+   |    |
#     |<-------x0------->    ^           y1   |
#     |                      |           |    |
#     |                     y0           |    |
#     |                      v           v    |
#     *---------------------------------------*
#
# Given in points (72 points = 1 inch = 25.4 mm)
TARGET_COOR_TOLERANCE = 65

# Define minimal figure size when extracting figures. If figure size is too small, it's not human readable.
# Given in points (72 points = 1 inch = 25.4 mm)
FIGURE_MIN_HEIGHT = 15
FIGURE_MIN_WIDTH = 15

#######################
# CHANGEABLE PARAMETERS
#######################

# Page margins used to crop pages. The default is 0, so page cropping is deactivated.
# This is a global variable because:
# - it is written in 2 places: initialization here and can be set from command line / API
# - it is used in multiple modules, passing around is cumbersome
PAGE_CROP_MARGINS = {
    "top": 0.0,
    "right": 0.0,
    "bottom": 0.0,
    "left": 0.0,
}

# Page margins used as a search area for smart header/footer detection.
# This is a global variable because:
# - it is written in 2 places: initialization here and can be set from command line / API
# - it is used in multiple modules, passing around is cumbersome
# Given as fraction of page height for top (header) and bottom (footer)
# Example: 0.2 (==20% of page height)
SMART_PAGE_CROP_REL_MARGINS = {
    "top": 0.2,
    "bottom": 0.2,
}

# Parameter for the extraction of potential header/footer elements.
# This parameter is given in percentage (range 0..1), e.g. an element will be considered a potential header/footer
# element if it appears on more than 30% of all pages.
HEADER_FOOTER_OCCURRENCE_PERCENTAGE = 0.3

# A real header/footer element has two attributes:
# - continuously occurs from page to page
# - same y0 coordinate for header/footer
# However some PDFs do not strictly follow this, that's why the following 3 parameters exist.
# They are used for smart header/footer detection to filter out falsely detected header/footer elements.
# The followed parameters are given in percentage (range 0..1):
# 1. the page missing header or footer percentage means, The maximal percentage of pages on which no header or footer
#    elements at all, e.g detected header or footer elements on page 2-20 except page 5 and page 9, cause on page 5 and
#    9, there are no header or footer elements at all, this is inside the 15% tolerance. This parameter is needed to
#    make sure the gap (page missing header or footer elements) is in tolerance before using the second parameter
#    HEADER_FOOTER_CONTINUOUS_PERCENTAGE in below to check the continuous
# 2. the header or footer element continuous percentage, used to check continuousness of detected header or footer
#    element, e.g. for pdf with only 4 pages, chapter headline on page 1 and page 3 are very close to header, they
#    appear on more than 30% of pdf pages, but they are not continuous. To check the continuousness of detected
#    potential header or footer element, this parameter HEADER_FOOTER_CONTINUOUS_PERCENTAGE is used, e.g. for the 4
#    pages pdf, detected potential header element: chapter headline, start page is 1, end page is 3, 3*0.8 = 2.4, which
#    means the detected potential header element should appear on more than 2.4 pages, but it only appears on page 1 and
#    3, so it's not header element
# 3. the unique header or footer elements is used for some pdfs, they have header or footer elements that are only
#    partially continuous, e.g. one detected header element appears on page 2-10, 20-30, 50-60, another detected header
#    element appears on page 2-60, these two detected elements are actually header elements, but the second parameter
#    HEADER_FOOTER_CONTINUOUS_PERCENTAGE will detect the element (appear on page 2-10, 20-30, 50-60) not as header
#    element. In order to solve this partially continuous header or footer element situation, this third parameter is
#    introduced, inside each header or footer on each page, they can have several elements with several unique y0
#    position, and they should be consistent though the whole pdf, hence, we check the amounts of unique header
#    elements. This parameter UNIQUE_HEADER_OR_FOOTER_ELEMENTS_PERCENTAGE is given in percentage, e.g. for the above
#    example, detected potential header element that appear on page 2-10, 20-30, 50-60, the maximal unique header
#    elements shall be 60*0.05 = 3, for small pdf, like only 4 pages, 4*0.05 = 0.2, which is smaller than 1, so the
#    minimal is 1. In a word, the unique header or footer element for the whole pdf should in range:
#    (1, pdf_pages * UNIQUE_HEADER_OR_FOOTER_ELEMENTS_PERCENTAGE)
PAGES_MISSING_HEADER_OR_FOOTER_PERCENTAGE = 0.15
HEADER_OR_FOOTER_CONTINUOUS_PERCENTAGE = 0.8
UNIQUE_HEADER_OR_FOOTER_ELEMENTS_PERCENTAGE = 0.05

# The following parameters are used for visual debugging
# Give colors a human readable name
COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (255, 255, 1),
}

# Map extracted elements with color
# the numbers at the end means transparency, the value should be set in range (40, 160)
VIS_DBG_MAP_ELEMENTS_COLOR = {
    "chapter": COLORS["green"] + (80,),
    "paragraph": COLORS["blue"] + (40,),
    "table": COLORS["red"] + (40,),
    "figure": COLORS["yellow"] + (80,),
    "rect": COLORS["cyan"] + (160,),
}

RENDER_ELEMENTS = [
    "chapter",
    "paragraph",
    "table",
    "figure",
    "rect",
]  # the elements that shall be rendered

# pdfminer layout analysis parameter from from pdfminer.layout -> LAParams.__init__
# These are needed for 2 reasons:
# - pdfplumber wrapper around pdfminer only requests layout analysis if at least one laparam is given
# - they are adapted to best practice values, the deviations are commented below
LA_PARAMS = {
    "line_overlap": 0.5,
    "char_margin": 6.0,  # default: 2.0
    "line_margin": 0.4,  # default : 0.5
    "word_margin": 0.1,
    "boxes_flow": 0.5,
    "detect_vertical": False,
    "all_texts": False,
}
