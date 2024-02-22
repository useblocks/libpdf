"""
Process the things which I don't know how to categorize.

It includes:
1. metadata of chars and lines process
2. annotation markup
3. elements sorting
4. yaml output
"""

import datetime
import decimal
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Union

import ruamel.yaml
from ruamel.yaml.representer import RoundTripRepresenter

from libpdf import parameters
from libpdf.apiobjects import ApiObjects
from libpdf.catalog import catalog
from libpdf.models.chapter import Chapter
from libpdf.models.element import Element
from libpdf.models.figure import Figure
from libpdf.models.link import Link
from libpdf.models.model_base import ModelBase
from libpdf.models.page import Page
from libpdf.models.paragraph import Paragraph
from libpdf.models.position import Position
from libpdf.models.rect import Rect
from libpdf.models.table import Cell, Table
from libpdf.parameters import HEADLINE_TOLERANCE

LOG = logging.getLogger(__name__)


def remove_page_header_footer(single_page):
    """Remove header and footer."""
    page_crop = single_page.within_bbox(
        (
            0,
            decimal.Decimal(parameters.PAGE_CROP_MARGINS["top"]),
            single_page.width,
            single_page.height
            - decimal.Decimal(parameters.PAGE_CROP_MARGINS["bottom"]),
        ),
    )

    return page_crop


class MyRepresenter(RoundTripRepresenter):  # pylint: disable=too-few-public-methods
    """Customized representer of yaml."""

    def represent_mapping(self, tag, mapping, flow_style=None):
        """Override represent_mapping."""
        tag = "tag:yaml.org,2002:map"

        return RoundTripRepresenter.represent_mapping(
            self, tag, mapping, flow_style=flow_style
        )


def to_dict_output(obj: Union[ModelBase, Position]) -> Dict:  # pylint: disable=too-many-branches  #easy to in one func
    """Turn all objects attributes into a dictionary."""
    vars_dict = vars(obj).copy()

    if isinstance(obj, (Chapter, Figure, Page, Paragraph, Table, Rect)):
        # insert id as first key into vars_dict
        # After python3.6/3.7, a dict is sorted in insertion order
        #     https://docs.python.org/3.6/whatsnew/3.6.html#whatsnew36-compactdict
        #     https://docs.python.org/3.7/tutorial/datastructures.html#dictionaries
        temp_dict = {"id": obj.id_}
        temp_dict.update(vars_dict)
        vars_dict = temp_dict
    if isinstance(obj, (Figure, Paragraph, Table, Rect)):
        # idx is not part of the UML model and should not be exported
        del vars_dict["idx"]
    if isinstance(obj, Page):
        # no serialization for the contents of pages
        del vars_dict["content"]
    if isinstance(obj, (Paragraph, Cell, Chapter, Rect)):
        # textboxes with positions are not interest of the output file
        if obj.textbox:
            text = obj.textbox.text
            vars_dict["text"] = text
        del vars_dict["textbox"]
    if isinstance(obj, (Figure)):
        # textboxes with positions are not interest of the output file
        if obj.textboxes:
            text = "\n".join(x.text for x in obj.textboxes)
            vars_dict["text"] = text
        del vars_dict["textboxes"]

    # delete back references so the export does not create circular loops
    delete_backref_keys = []
    for key in vars_dict:
        if key.startswith("b_"):
            delete_backref_keys.append(key)
    for key in delete_backref_keys:
        del vars_dict[key]

    for key, value in vars_dict.items():
        if isinstance(value, (ModelBase, Position)):
            # recurse directly
            vars_dict[key] = to_dict_output(value)
        elif isinstance(value, list):
            # iterate and then recurse
            for index, element in enumerate(value):
                if isinstance(element, (ModelBase, Position)):
                    vars_dict[key][index] = to_dict_output(element)

    if "page" in vars_dict:
        # according to the model pages are serialized as page.<number>
        # this supports the common adressing scheme in libpdf
        vars_dict["page"] = vars_dict["page"]["id"]

    return vars_dict


def json_datetime_converter(obj):
    """Serialize datetime instance for JSON."""
    if isinstance(obj, datetime.datetime):
        return str(obj)
    return obj


def output_dump(output_format: str, output_path: str, objects: ApiObjects):
    """
    Dump the extracted content into a yaml file.

    :param output_format:
    :param output_path:
    :param objects:
    :return:
    """
    # TODO docstring incomplete
    ruamel_yaml = ruamel.yaml.YAML()
    ruamel_yaml.Representer = MyRepresenter
    ruamel_yaml.indent(sequence=4, offset=2)
    # # ruamel_yaml.representer.ignore_aliases = lambda *data: True
    #
    # ruamel_yaml.register_class(Table)
    # ruamel_yaml.register_class(Position)
    # ruamel_yaml.register_class(Page)
    # ruamel_yaml.register_class(Root)
    # ruamel_yaml.register_class(File)
    # ruamel_yaml.register_class(FileMeta)
    # ruamel_yaml.register_class(Paragraph)
    # ruamel_yaml.register_class(Chapter)
    # ruamel_yaml.register_class(Cell)

    output_dict = {"root": to_dict_output(objects.root)}

    if output_path is None:
        LOG.info("Writing extracted data to stdout")
        if output_format == "json":
            print(
                json.dumps(
                    output_dict,
                    default=json_datetime_converter,
                    indent=2,
                    sort_keys=False,
                )
            )
        elif output_format == "yaml":
            ruamel_yaml.dump(output_dict, sys.stdout)
    else:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
        with open(output_path, "w", encoding="utf-8") as file:
            if output_format == "json":
                json_string = json.dumps(
                    output_dict,
                    default=json_datetime_converter,
                    indent=2,
                    sort_keys=False,
                )
                file.write(json_string)
            elif output_format == "yaml":
                ruamel_yaml.dump(output_dict, file)


def merge_all_elements(*elements):
    """
    Merge all the elements in to a list in a flatten structure and they are sorted by pages and y coordinate.

    :param elements:
    :return:
    """
    element_list = []
    for element in elements:
        if len(element) > 0:
            for obj in element:
                element_list.append(obj)

    element_list.sort(
        key=lambda x: (
            x.position.page.number,
            (float(x.position.page.height) - x.position.y0),
        )
    )

    return element_list


def filter_out_outline_page(outline_dict):
    """Filter out outline whose target page are not in the extracted pages list."""
    for outline_chapter in outline_dict["content"].copy():
        if outline_chapter["position"]["page"] is None:
            outline_dict["content"].remove(outline_chapter)
        # recursively check subchapter
        if outline_chapter["content"]:
            filter_out_outline_page(outline_chapter)
    return outline_dict


def map_elements_outline(
    element_list: List[Union[Chapter, Figure, Table, Paragraph, Rect]],
    outline_dict,
) -> List[Union[Chapter, Figure, Table, Paragraph, Rect]]:
    """
    Map elements into a nested outline structure.

    :param element_list: a list of elements including chapters, figures, rects, tables, and paragraphs in a flatten structure.
    :param outline_dict: a nested outline structure from catalogs.
    :return:
    """
    # filter out outline whose target page are not in the extracted pages list
    filter_out_outline_page(outline_dict)

    if outline_dict["content"]:
        elements_above_outline = list(
            filter(
                lambda x: x.position.page.number
                < outline_dict["content"][0]["position"]["page"]
                or (
                    x.position.page.number
                    == outline_dict["content"][0]["position"]["page"]
                    and x.position.y1
                    > outline_dict["content"][0]["position"]["y1"] + HEADLINE_TOLERANCE
                ),
                element_list,
            ),
        )

        elements_in_outline = list(
            filter(
                lambda x: x.position.page.number
                > outline_dict["content"][0]["position"]["page"]
                or (
                    x.position.page.number
                    == outline_dict["content"][0]["position"]["page"]
                    and x.position.y1
                    < outline_dict["content"][0]["position"]["y1"] + HEADLINE_TOLERANCE
                ),
                element_list,
            ),
        )
    else:
        # all the elements are all above outline
        elements_above_outline = element_list
        elements_in_outline = []

    # elements_in_outline must start with chapter
    for idx, elem in enumerate(elements_in_outline):
        if isinstance(elem, Chapter):
            elements_above_outline.extend(elements_in_outline[:idx])
            del elements_in_outline[:idx]
            break

    # acquire a list of chapters where their contents are filled with the corresponding elements, figures, rects, tables
    # and paragraphs. This chapter list is still in a flatten structure
    chapters_content_filled = fill_elements_content(elements_in_outline)

    # turn chapters in a flatten structure into nested one
    nested_chapters: List[Chapter] = []

    mapping_chapters(
        chapters_content_filled,
        nested_chapters,
        outline_content=outline_dict["content"],
        b_chapter=None,
    )

    # elements below the outline
    nested_elements = elements_above_outline + nested_chapters

    return nested_elements


def fill_elements_content(
    elements_in_outline: List[Union[Chapter, Figure, Rect, Table, Paragraph]],
) -> List[Chapter]:
    """
    Fill the elements, tables, figures, rects and paragraphs into their corresponding chapters' contents.

    The back chapter's reference of tables, figures, and paragraphs are added in this function

    :param elements_in_outline: a list of elements covered by the outline.
    :return: a list of chapters in a flatten structure.
    """
    for index_element, element in enumerate(elements_in_outline):
        if isinstance(element, Chapter):
            id_dict = {"table": 1, "figure": 1, "paragraph": 1, "rect": 1}
            content = element.content
            index_b_chapter = index_element
        elif "content" in locals():
            element.idx = id_dict[element.type]
            element.b_chapter = elements_in_outline[index_b_chapter]
            content.append(element)
            id_dict[element.type] += 1
        else:
            # TODO 1. this exception is not caught in libpdf code and will go all the way up to the user (wanted?)
            #      2. the message is unclear
            #      3. if it's a programming error, fix the code
            #      4. if it's a real runtime issue coming from wrong PDF input, catch the error one level above
            #         and log an understandable, critical error
            raise ValueError(
                "elements can not fill into the content because it does not exist"
            )

    chapters_content = list(
        filter(lambda x: isinstance(x, Chapter), elements_in_outline)
    )

    return chapters_content


def mapping_chapters(
    chapters_content_filled: List[Chapter],
    nested_chapters: List,
    outline_content,
    b_chapter: Optional[Chapter],
):
    """
    Map flatten chapters into a nested outline structure recursively.

    The function traverses the chapters in the outline and check if the position of any chapter in a flatten structure
    matches the current chapter's position.

    :param chapters_content_filled: A list of flatten chapters with content filled with corresponding elements
                                    apart from chapters.
    :param nested_chapters: A list of nested chapters
    :param outline_content: A outline where chapters' headlines are nested.
    :param b_chapter: A back reference chapter
    :return:
    """
    for outline_chapter in outline_content:
        # use a list to contain the filtered chapter because I don't know how to process a filtered object.
        # check if the title and page number are matched.
        filter_chapter = [
            x
            for x in chapters_content_filled
            if x.title == outline_chapter["title"]
            and x.number == outline_chapter["number"]
        ]

        # Presumably, there is only one chapter matched in a flatten structure
        if not filter_chapter:
            # TODO this is not a good log message
            #      1. as a developer, I don't understand it
            #      2. the message is for end users but it contains an internal variable elements_in_outline
            #      3. level is DEBUG but it looks like a problem
            LOG.debug(
                "The expected element %s may be not in elements_in_outline",
                outline_chapter["title"],
            )

            # raise ValueError('No filtered chapter found. The expected element may be not in elements_in_outline')
            continue

        filter_chapter[0].b_chapter = b_chapter
        nested_chapters.append(filter_chapter[0])
        index_chapter = len(nested_chapters) - 1

        if outline_chapter["content"]:  # next deeper level
            if isinstance(nested_chapters[index_chapter], Chapter):
                mapping_chapters(
                    chapters_content_filled,
                    nested_chapters[index_chapter].content,
                    outline_chapter["content"],
                    b_chapter=nested_chapters[index_chapter],
                )
            else:
                LOG.debug(
                    "Non-Chapter object %s is detected",
                    nested_chapters[index_chapter].id,
                )


def libpdf_target_explorer(  # pylint: disable=too-many-nested-blocks # local algorithm, better readability
    elements: List[Union[Paragraph, Table]],
    pages_list: List[Page],
):
    """
    Convert the name_destination/target_link to nest ID paths.

    Target links are inserted on the first stage of linked_chars extraction and these are in the forms of
    either implicit (name destination) or explicit target (position), so these target links require the
    conversion. The first stage happens when paragraphs or tables are rendered.

    The conversion consists of the following steps:

    1. find a page where annos (source links) occur
    2. find elements on the page containing annos
    3. find the elements containing annos
    4. extract the annos of the element
    5. find the element directed by the target link of the anno
    6. convert the target_link (positions or name destinations) in the annos to hierarchical element's ID paths

    The results of the conversion will be directly applied in the input list 'elements'.

    :param elements: a list of paragraphs or tables, where the results of conversion are directly applied.
    :param pages_list: a list of pages referred by the elements
    """
    # find the page containing source links
    for page in pages_list:
        if page.number in catalog["annos"]:
            elements_on_page = [
                x for x in elements if x.position.page.number == page.number
            ]

            # find the elements which contains source links on a certain page
            elements_with_anno = elements_with_anno_finder(elements_on_page)

            if elements_with_anno:
                for element in elements_with_anno:
                    if len(element.links) > 0:
                        for link in element.links:
                            target_id = find_target_id(link, pages_list, element)
                            link.libpdf_target = target_id
                    elif isinstance(element, Cell):
                        # Cell is not considered as element
                        pass
                    else:
                        # TODO reason about the overall logic; which cases can be removed? distinguish between
                        #      programming errors (raise RuntimeErrors) and cases that actually may exist in the
                        #      wild and write human-readable log messages (e.g.
                        #        The link on page xy with text xy cannot be resolved to a libpdf element; linking
                        #        to the target page position instead
                        LOG.error(
                            "The source link in the paragraph %s is missing",
                            repr(element),
                        )


def elements_with_anno_finder(
    elements_on_page: List[Union[Paragraph, Table]],
) -> Union[List[Union[Chapter, Paragraph, Figure, Rect, Table, Cell]], None]:
    """
    Find the elements, tables or paragraphs containing source links.

    The function use two nested loop to collect the elements containing annos. As longs as an element
    containing an anno is found, this element will be popped out from the searching list.

    The algorithm still has room to improve for the runtime.

    :param elements_on_page: a list of elements on a certain page
    :param anno_page: a list of annotations (source links) on a certain page
    :return: a list of elements containing annotations
    """
    if not elements_on_page:
        return None

    elements_with_anno = []

    if isinstance(elements_on_page[0], Table):
        flatten_cells = []
        for table in elements_on_page:
            flatten_cells.extend(table.cells)

        elements_on_page = flatten_cells

    for element in reversed(elements_on_page):
        # check if the element contains links
        if element.links:
            elements_with_anno.append(element)
            elements_on_page.remove(element)

    return elements_with_anno


def find_target_id(link: Link, pages_list: List[Page], src_element: Element) -> str:
    """
    Find the corresponding libpdf target element ID from positions.

    :param target_name: custom string representation of the PDF named destination or explicit target;
                        example for named destination: ``section1.1``;
                        example for explicit target: ``page: 4 rect_X: 300 rect_Y: 400``
    :param pages_list: list of libpdf pages
    :param src_element: the element that contains the source link, for logging purposes
    :return: libpdf target ID if the target element is found, otherwise a string representing the
             page with the x/y coordinate of the destination
    """
    target_id = None

    if link.pos_target["page"]:
        for page in pages_list:
            if page.number == link.pos_target["page"]:
                target_page = page
        # target_page = pages_list[link.pos_target['page'] - 1]
        elements_target_page = get_elements_page(target_page)
        for element in elements_target_page:
            if element.contains_coord(
                link.pos_target["page"], link.pos_target["x"], link.pos_target["y"]
            ):
                target_id = nest_explorer(element)
                break

        if not target_id:
            # If no libpdf element is found,
            # the target is set to the target coordinates given as page.<id>/<X>:<Y>
            # To improve element detection, the parameter TARGET_COOR_TOLERANCE may need to be adjusted
            target_id = (
                f'{target_page.id_}/{link.pos_target["x"]}:{link.pos_target["y"]}'
            )

            text = str(src_element)
            text_shortened = (text[:60] + "..") if len(text) > 60 else text
            LOG.debug(
                'The link "%s" on page %s could not be resolved to a libpdf element; replacing it with the raw '
                "target page coordinate %s",
                text_shortened,
                src_element.position.page.number,
                target_id,
            )
    else:
        target_id = "Out Of extracted pages scope"

    return target_id


def get_elements_page(target_page: Page) -> List[Union[Paragraph, Table, Figure, Rect]]:
    """
    Collect the elements, which occurs on a certain target page.

    :param target_page: a page which is directed to by target links
    :return: a list of elements on a target page
    """
    elements_target_page = []
    for position in target_page.b_positions:
        # b_element for Cell is None
        if position.b_element:
            elements_target_page.append(position.b_element)

    return elements_target_page


def nest_explorer(element: Union[Figure, Rect, Table, Chapter, Paragraph]) -> str:
    """
    Explore the nested target ID path recursively.

    :param element: a target element on a certain level of the hierarchy
    :return: element ID with a hierarchical path
    """
    if element.b_chapter:
        element_id = nest_explorer(element.b_chapter)
        element_id = element_id + "/" + element.id_
    else:
        element_id = element.id_

    return element_id
