.. _uml_pdf_model:

UML PDF model
=============

.. uml::

    @startuml

        skinparam object {
            AttributeFontSize 11
        }

        ' increase distance between nodes
        skinparam nodesep 50

        ' default arrow color and arrow font color
        !define COL_ARROW_DEFAULT darkblue
        skinparam arrowcolor COL_ARROW_DEFAULT
        skinparam arrowfontcolor COL_ARROW_DEFAULT

        ' color of arrows showing inheritance
        !define COL_DERIVE red

        class Root {
        --
        **content**: container for elements of type
        ""Chapter/Table/Figure/Paragraph""
        --
        **library/API**: All ""Root"" elements are exposed as given in this diagram.

        **CLI/YAML/JSON**: ""Root.pages"" contain a list of ""Page"" instances without
        ""Page.contents"" attribute. Instead, all content goes to ""Root.contents""
        and the nested ""Chapter.contents"".
        }

        class Element {
            + [str] id
            + [str] type
            --
            **id**: unique in given scope (root or chapter)
            **type**: parent class name

            **b_root**: set, if the element
            is directly located under root
            **b_chapter**: set, if the element
            is located under a chapter
        }

        class Position {
            + [float] x0
            + [float] y0
            + [float] x1
            + [float] y1
            --
            **page**: reference to a ""Page"" instance;
            For YAML/JSON output it is serialized to
            an attribute holding ""Page.id""

            ""Position"" is either referenced by a ""Cell""
            or by an ""Element"" (never both).
            **b_cell**: set, if the Position is referenced
            by a ""Cell""
            **b_element**: set, if the Position is
            referenced by an ""Element""
        }

        class File {
            + [str] id
            + [str] name
            + [str] path
            + [int] page_count
            + [float] crop_top [points]
            + [float] crop_bottom [points]
            + [float] crop_left [points]
            + [float] crop_right [points]
            --
            **id**: ""file.<name-as-identifier>""
        }

        class FileMeta {
            + [str] author
            + [str] title
            + [str] subject
            + [str] creator
            + [str] producer
            + [str] keywords
            + [utc_date] creation_date
            + [utc_date] modified_date
            + [bool] trapped
        }

        class Page {
            + [str] id
            + [int] number
            + [float] width [points]
            + [float] height [points]
            --
            **id**: ""page.<1,2,3,n>""
            **number**: 1-based
            **content**: container for elements of type
            ""Chapter/Table/Figure/Paragraph""
        }

        class Link {
            + [int] idx_start
            + [int] idx_end
            + [dict] pos_target
            + [str] libpdf_target
            --
            **pos_target**: it's a dictionary with the position info
            e.g.
                      page: 3,
                      x: 300.454
                      y: 300.454

            **libpdf_target**: points either to an ""Element"" or
            to a ""Page"". The link is built by concatenating
            nested elements separated by '/', e.g.
            ""  chapter.3/chapter.3.2/table.2""
            For case where the pos_target can not be resolved,
            the target is set to the target coordinates given as page.<id>/<X>:<Y>
            ""  page.4/56:789 ""
        }

        class Paragraph {
            + [str] text: content of the Paragraph
            --
            **id**: ""paragraph.<1,2,3,n>""
            A paragraph gets detected by
            layout analysis. Characters are
            merged into words, words into
            lines and lines into paragraphs.
            A new word, line or paragraph
            is started if the gap changes
            significantly.
        }

        class Chapter {
            + [str] title
            + [str] number
            --
            **id**: ""chapter.<number>""
            **number**: globally unique (e.g. 3.2.4)
            **content**: container for elements of type
            ""Chapter/Table/Figure/Paragraph""
        }

        class Cell {
            + [int] row
            + [int] col
            + [str] text: Cell content
            --
            **row**: 1-based
            **col**: 1-based
        }

        class Table {
            --
            **id**: ""table.<1,2,3,n>""
        }

        class Figure {
            + [str] rel_path
            + [str] caption
            + [str] text: text inside Figure area
            --
            **id**: ""figure.<1,2,3,n>""
            **rel_path**: figures/<image>
        }

        Paragraph "+b_source  1" *-- "+links  *" Link
        Figure "+b_source  1" *-- "+links  *" Link
        Cell "+b_source  1" *-- "+links  *" Link

        Cell "+cells  1..*" --* "+b_table  1" Table
        Cell "+b_cell  1" *-- "+position  1" Position

        Table -[#COL_DERIVE]-|> Element
        Figure -[#COL_DERIVE]-|> Element
        Chapter -[#COL_DERIVE]-|> Element
        Paragraph -[#COL_DERIVE]-|> Element

        Chapter "1" *-- "+content  *" Element: ordered
        Page "1" *-- "+content  *" Element: ordered

        ' all root structures derive from Element
        Position "+position  1" --* "+b_element  1" Element
        Element "+content *" --* "+b_root  1" Root: ordered
        File "+file  1" --* "+b_root  1" Root
        Page "+pages  1..*" --* "+b_root  1" Root
        Position "+b_positions  *" --* "+page  1" Page
        FileMeta "+file_meta  1" --* "+b_file  1" File

    @enduml
