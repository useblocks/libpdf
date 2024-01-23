"""Test figures extraction."""
from click.testing import CliRunner

import libpdf
from libpdf.apiobjects import ApiObjects, Chapter, Rect

from tests.conftest import (
    PDF_RECTS_EXTRACTION,
)

import logging
from typing import Any, Dict, List, Tuple


def find_chapter(objects: ApiObjects, chapter_name: str) -> Chapter:

    chapters = objects.flattened.chapters
    ret_chapter = None
    assert 0 < len(chapters)
    for chapter in chapters:
        if chapter.title == chapter_name:
            ret_chapter = chapter

    assert ret_chapter is not None
    return ret_chapter


def chapter_contains_code_with_text(chapter: Chapter, text: str, color: Tuple[float], margin_text:int = 0) -> bool:
    page = chapter.position.page.number
    # check chapter content
    assert chapter.content is not None
    para_textbox = None
    rect_textbox = None

    #rects = pdf_info[KEY_OBJECTS].flattened.rects
    #for rect in rects:
    #    if rect.position.page.number == page:
    #        logging.info(f"chapter_contains_code_with_text: {rect}")

    for content in chapter.content:
        if content.type in ["paragraph", "rect"]:
            if text in content.textbox.text:
                assert content.textbox.x0 +  margin_text >= chapter.position.x0
                logging.debug(f"textbox paragraph = {content.textbox.x0} {content.textbox.x1} {content.textbox.lines}")
                if content.type == "rect":
                    assert content.non_stroking_color == color
                    rect_textbox = content.textbox
                else:
                    para_textbox = content.textbox

    if para_textbox is not None and rect_textbox is not None:
        assert(para_textbox.x0 <= rect_textbox.x0)

    return para_textbox is not None and rect_textbox is not None


def test_rects_extraction():
    """Remove figures, which are completely inside other figures, from extracted figures list."""
    objects = libpdf.load(PDF_RECTS_EXTRACTION)
    assert objects.flattened.rects is not None

    chapter = find_chapter(objects, "Code Block Highlighting")
    assert chapter is not None
    assert chapter_contains_code_with_text(chapter, "def decode_title(obj_bytes: bytes) -> str:", (0.941176, 0.941176, 0.941176))
    

    chapter = find_chapter(objects, "Code Inline Highlighting")
    assert chapter_contains_code_with_text(chapter, "from pathlib import Path", (0.945098, 0.945098, 0.945098), margin_text = 234)
    
 
