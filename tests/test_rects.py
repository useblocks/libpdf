"""Test rects extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from os import PathLike

    from libpdf.apiobjects import ApiObjects, Chapter, Paragraph, Rect

import libpdf
from tests.conftest import (
    PDF_RECTS_EXTRACTION,
)


def find_chapter(objects: ApiObjects, chapter_name: str) -> Chapter:
    """
    search for given chapter in the objects.

    :return: found chapter
    """
    chapters = objects.flattened.chapters
    ret_chapter = None
    assert len(chapters) > 0
    for chapter in chapters:
        if chapter.title == chapter_name:
            ret_chapter = chapter

    assert ret_chapter is not None
    return ret_chapter


def check_chapter_contains_text_paragraph(
    chapter: Chapter, text: str
) -> [Paragraph | None]:
    """
    check for text in chapter paragraphs.

    :return: found paragraph
    """
    assert chapter.content is not None

    for content in chapter.content:
        if content.type == "paragraph" and text in content.textbox.text:
            return content

    return None


def check_chapter_contains_text_rect(chapter: Chapter, text: str) -> [Paragraph | None]:
    """
    check for text in chapter rects.

    :return: found rect
    """
    assert chapter.content is not None

    for content in chapter.content:
        if content.type == "rect" and text in content.textbox.text:
            return content

    return None


def check_chapter_rects_count(chapter: Chapter) -> int:
    """
    check for number of rects in chapter.

    :return: number of rects
    """
    assert chapter.content is not None
    count = 0

    for content in chapter.content:
        if content.type == "rect":
            count += 1

    return count


def check_content_color(content: Rect, color: Sequence[int]) -> bool:
    """
    check rect color is equal given color.

    :return: True if equal
    """
    return content.non_stroking_color == color


def check_content_margins_equal(rect: Rect, paragraph: Paragraph) -> bool:
    """
    check for text margins between rect and paragraph.

    :return: True if x0 equals
    """
    return paragraph.textbox.x0 == rect.textbox.x0


def check_content_margins_greater(
    rect: Rect, paragraph: Paragraph, offset: int
) -> bool:
    """
    check for text margins of given rect.x0 + offset is greater or equal paragraph x0.

    :return: found paragraph
    """
    return rect.textbox.x0 + offset >= paragraph.textbox.x0


def test_rects_extraction_code_block() -> None:
    """Test rect extraction of multiline codeblock."""
    smart_page_crop = (
        True  # remove header and footers so rects IN chapters are left only.
    )

    objects = libpdf.load(PDF_RECTS_EXTRACTION, smart_page_crop=smart_page_crop)
    assert objects.flattened.rects is not None

    chapter = find_chapter(objects, "Code Block Highlighting")

    assert chapter is not None

    assert check_chapter_rects_count(chapter) == 1

    paragraph = check_chapter_contains_text_paragraph(
        chapter, "def decode_title(obj_bytes: bytes) -> str:"
    )
    assert paragraph is not None

    rect = check_chapter_contains_text_rect(
        chapter, "def decode_title(obj_bytes: bytes) -> str:"
    )
    assert rect is not None

    assert check_content_color(rect, (0.941176, 0.941176, 0.941176))

    assert check_content_margins_equal(paragraph, rect)


def test_rects_extraction_code_inline() -> None:
    """Test rect extraction of inline codeblock."""
    smart_page_crop = (
        True  # remove header and footers so rects IN chapters are left only.
    )

    objects = libpdf.load(PDF_RECTS_EXTRACTION, smart_page_crop=smart_page_crop)
    assert objects.flattened.rects is not None

    chapter = find_chapter(objects, "Code Inline Highlighting")

    # 2 inline code blocks, but the first one is broken in two lines
    assert check_chapter_rects_count(chapter) == 1 * 3

    paragraph = check_chapter_contains_text_paragraph(
        chapter, "from pathlib import Path"
    )
    assert paragraph is not None

    rect = check_chapter_contains_text_rect(chapter, "from pathlib import Path")
    assert rect is not None
    assert rect.textbox.text == "from pathlib import Path"
    assert check_content_color(rect, (0.945098, 0.945098, 0.945098))
    assert check_content_margins_greater(rect, paragraph, 234)

    assert (
        check_chapter_contains_text_rect(
            chapter, "decode_title(obj_bytes: bytes) -> str"
        )
        is None
    )
    rect = check_chapter_contains_text_rect(chapter, "decode_title(obj_bytes: bytes)")
    assert rect is not None
    rect_str = check_chapter_contains_text_rect(chapter, "str ")
    assert rect_str is not None

    assert rect_str.textbox.x0 < rect.textbox.x0


def test_rects_extraction_adminition() -> None:
    """Test rect extraction of 3 admonitions."""
    smart_page_crop = (
        True  # remove header and footers so rects IN chapters are left only.
    )

    objects = libpdf.load(PDF_RECTS_EXTRACTION, smart_page_crop=smart_page_crop)
    assert objects.flattened.rects is not None

    chapter = find_chapter(objects, "Adminition")

    assert (
        check_chapter_rects_count(chapter) == 3 * 2
    )  # 2 rects per admonition, 3 types of admonition

    rect = check_chapter_contains_text_rect(chapter, "A very importing Adminition")
    assert rect is not None
    assert check_content_color(rect, (0.858824, 0.980392, 0.956863))

    rect_inner = check_chapter_contains_text_rect(chapter, "Wichtig")
    assert rect_inner is not None
    assert check_content_color(rect, (0.858824, 0.980392, 0.956863))


def test_rects_extraction_table(tmpdir: PathLike) -> None:
    """Test rect extraction of table colored cells."""
    smart_page_crop = (
        True  # remove header and footers so rects IN chapters are left only.
    )

    objects = libpdf.load(
        PDF_RECTS_EXTRACTION,
        smart_page_crop=smart_page_crop,
        visual_debug=True,
        visual_debug_output_dir=tmpdir.join("visual_debug_dir"),
        visual_split_elements=True,
    )
    assert objects.flattened.rects is not None

    chapter = find_chapter(objects, "Tables")

    assert (
        check_chapter_rects_count(chapter) == 1 * 5
    )  # would expect 7 (3 from each colored table line + 1 inline code)
