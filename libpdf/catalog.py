"""PDF catalog extraction."""
import logging
import re
from typing import Any, Dict, List, Union

from pdfminer.pdftypes import PDFObjRef, resolve1
from pdfminer.psparser import PSLiteral

from libpdf.log import logging_needed
from libpdf.parameters import ANNO_X_TOLERANCE, ANNO_Y_TOLERANCE
from libpdf.progress import bar_format_lvl2, tqdm
from libpdf.utils import decode_title, to_pdfplumber_bbox

LOG = logging.getLogger(__name__)


catalog = {
    'outline': {},
    'annos': {},
    'dests': {},
}


def get_named_destination(pdf):  # pylint: disable=too-many-branches
    """Extract Name destination catalog.

    Extracts Name destination catalog (link target) from pdf.doc.catalog['Name'] to obtain
    the coordinates (x,y) and page for the corresponding destination's name.

    PDFPlumber does not provide explict 'Named Destinations of Document Catalog' like py2pdf, so it needs to be obtained
    by resolving the hierarchical indirect objects.

    The first step in this function is to check if the name destination exist in the PDF. If it does not, no extraction
    is executed.

    :param pdf: pdf object of pdfplumber.pdf.PDF
    :return: named destination dictionary mapping reference of destination by name object
    """
    LOG.info('Catalog extraction: name destination ...')

    # check if name tree exist in catalog and extract name tree
    name_tree = {}
    named_destination = {}
    pdf_catalog = pdf.doc.catalog
    if 'Names' in pdf_catalog:
        # PDF 1.2
        if isinstance(pdf_catalog['Names'], PDFObjRef) and 'Dests' in pdf_catalog['Names'].resolve():
            name_tree = pdf_catalog['Names'].resolve()['Dests'].resolve()
        elif isinstance(pdf_catalog['Names'], dict) and 'Dests' in pdf_catalog['Names']:
            name_tree = resolve1(pdf_catalog['Names']['Dests'])
            # name_tree = pdf_catalog['Names']['Dests'].resolve()
            # LOG.debug(f"{name_tree}")
        # check if name tree not empty
        if name_tree:
            # map page id to page number
            page_id_num_map = {}
            for page in pdf.pages:
                page_id_num_map[page.page_number] = page.page_obj.pageid

            # If key "Kids" exists, it means the name destination catalog is nested in more than one hierarchy.
            # In this case, it needs to be flatten by the recursive function resolve_name_obj() for further process.
            # name_obj_list always contains a flatten name destination catalog.

            # resolve name objects
            if 'Kids' in name_tree:
                kids_hierarchy = []
                kids_hierarchy.extend([kid.resolve() for kid in name_tree['Kids']])
                name_obj_list = resolve_name_obj(kids_hierarchy)
            else:
                name_obj_list = [name_tree]

            for index_dest, item_dest in enumerate(name_obj_list):
                # In 'Names', odd indices are destination's names, while even indices are the obj id which can be
                # referred to the certain page in PDF
                for index_name in range(0, len(item_dest['Names']), 2):
                    named_destination[name_obj_list[index_dest]['Names'][index_name].decode('utf-8')] = name_obj_list[
                        index_dest
                    ]['Names'][index_name + 1]
    elif 'Dests' in pdf_catalog:
        # PDF 1.1
        if isinstance(pdf_catalog['Dests'], PDFObjRef):
            named_destination = pdf_catalog['Dests'].resolve()
        elif isinstance(pdf_catalog['Dests'], dict):
            named_destination = pdf_catalog['Dests']
    else:
        LOG.debug('Catalog extraction: name destinations do not exist')
        return None

    for key_object in named_destination:
        # only resolve when the value of named_destination is instance of PDFObjRef
        if isinstance(named_destination[key_object], PDFObjRef):
            named_destination[key_object] = named_destination[key_object].resolve()

    for key_name_dest in named_destination:
        # get the page number and the coordinate for the destination
        if 'D' not in named_destination[key_name_dest]:
            # the value of named_destination is a list, contains explict destination
            explict_dest = get_explict_dest(pdf, named_destination[key_name_dest])
        else:
            # the value of named_destination is a dictionary with a D entry, whose value is a list like above
            explict_dest = get_explict_dest(pdf, named_destination[key_name_dest]['D'])

        named_destination[key_name_dest] = {}
        named_destination[key_name_dest] = {
            'X': explict_dest[1],
            'Y': explict_dest[2],
            'Num': explict_dest[0],
        }

    return named_destination


def resolve_name_obj(name_tree_kids):
    """Resolve 'Names' objects recursively.

    If key 'Kids' exists in 'Names', the name destination is nested in a hierarchical structure. In this case, this
    recursion is used to resolve all the 'Kids'

    :param name_tree_kids: Name tree hierarchy containing kid needed to be solved
    :return: Resolved name tree list
    """
    temp_list = []
    for kid in name_tree_kids:
        if 'Kids' in kid and kid['Kids']:
            temp_list.extend([kid_kid.resolve() for kid_kid in kid['Kids']])
        elif 'Names' in kid:
            return name_tree_kids

    return resolve_name_obj(temp_list)


def get_outline(pdf, des_dict):
    """
    Extract outline catalog from pdf.doc.catalog['Outlines'].

    In this function, outline extraction needs to acquire the coordinates of chapters from name destination.
    In this case, if name destination doesn't exist, the outline is presumably not available either.

    Outline is firstly resolved to obtain first level of outline hierarchy. Afterwards, it will be fed into
    the recursive function resolve_outline(). The recursion takes care of the rest of outline hierarchy.

    :param pdf: pdf object extracted from PDF plumber
    :param des_dict: the dictionary of name destination
    :return: outline dictionary in a nested structure with each chapter's coordinates (x0, y0) and pages
    """
    LOG.info('Catalog extraction: outline ...')

    # check if outlines exist in catalog
    if 'Outlines' not in pdf.doc.catalog:
        LOG.info('Catalog extraction: outline does not exist...')
        return None

    # check if outline dictionary not empty
    if not pdf.doc.catalog['Outlines'].resolve():
        LOG.info('Catalog extraction: outline exists but is empty...')
        return None

    # TODO: why need dictionary with only one key here??? Can I change to list? This may affect downstream
    outlines = {'content': []}

    outline_obj = pdf.doc.catalog['Outlines'].resolve()
    if 'First' not in outline_obj:
        raise ValueError('Key "First" is not in Outlines')

    resolve_outline(outline_obj['First'].resolve(), outlines['content'], des_dict, pdf)

    if outlines['content']:
        chapter_number_giver(outlines['content'], '1')

    return outlines


def chapter_number_giver(chapters_in_outline: List[Dict], virt_hierarchical_level: str) -> None:
    """
    Assign chapter number to each chapter from the index in its title or the hierarchical level on the outline.

    The change will be directly applied in the list "chapters_in_outline". The function is recursive to
    explore to chapter hierarchy.

    :param chapters_in_outline: a list of nested chapters extracted from outline catalog
    :param virt_hierarchical_level: the current level of the outline hierarchy aka virtual number
    :return: None
    """
    levels = virt_hierarchical_level.split('.')
    start_level = int(levels[-1])  # last item in virt_hierarchical_level
    parent_level = '.'.join((levels[0:-1]))  # all but last item in virt_hierarchical_level
    for idx_chapter, chapter in enumerate(chapters_in_outline):
        current_level = start_level + idx_chapter

        if parent_level:
            new_hierarchical_level = f'{parent_level}.{current_level}'
        else:
            new_hierarchical_level = f'{current_level}'

        # remove leading spaces
        chapter_title = chapter['title'].strip()

        # match chapter number/index if exist, supported titles may contain a-z, A-Z, 0-9 and lower/upper case
        # roman numbers, separated by dots, e.g. 1.2.3 | 2.a.i | 2.a.IV | 1.2.3. | A | A.a.2
        pattern = re.compile(r'^(?!\.)((^|\.)(([iIvVxX]{1,8})|[a-zA-Z]|[0-9]+))+\.?(?=[ \t]+\S+)')
        chapter_number = re.match(pattern, chapter['title'].strip())

        if chapter_number:
            #  The assumption is that only one match is found
            chapters_in_outline[idx_chapter].update({'number': chapter_number[0]})
            chapters_in_outline[idx_chapter].update({'title': chapter_title.replace(chapter_number[0], '', 1).strip()})
        else:
            chapters_in_outline[idx_chapter].update({'number': f'virt.{new_hierarchical_level}'})

        if chapter['content']:
            # next deeper level
            chapter_number_giver(chapters_in_outline[idx_chapter]['content'], f'{new_hierarchical_level}.1')


def resolve_outline(outline_obj, outline_list, des_dict, pdf):  # pylint: disable=too-many-branches, too-many-statements
    """
    Resolve outline hierarchy from top level to furthest level recursively.

    In the outline hierarchy:

    *   'First' represents the first child of the current outline hierarchy. If First exists,
        it means the function has to recurse one level deeper.
    *   'Next' means the next item at the same outline level

    In this recursion, it will reach the deepest level first and then go up until all chapters are resolved.

    :param outline_obj: the object resolved from either 'First' or 'Next'
    :param outline_list: the reference of the certain level in the nested outline list
    :param des_dict: the dictionary of name destination
    :param pdf: pdfplumber.pdf.PDF object
    :return: outline list
    """
    # check if outline_obj['A'] and outline_obj['Dest'] coexist
    if 'A' in outline_obj and 'Dest' in outline_obj:
        LOG.error('Key A and Dest can not coexist in outline.')
        raise ValueError('Key A and Dest can not coexist in outline.')

    # get outline destination
    if 'A' in outline_obj:
        # make sure outline_obj['A'] is resolved
        if isinstance(outline_obj['A'], PDFObjRef):
            outline_dest_entry = outline_obj['A'].resolve()
        else:
            outline_dest_entry = outline_obj['A']

        # consider only go-to action, used for various targets in PDF standard
        if outline_dest_entry['S'].name == 'GoTo':
            if isinstance(outline_dest_entry['D'], list):
                # explict destination
                if isinstance(outline_dest_entry['D'][0], PDFObjRef):
                    explict_dest = get_explict_dest(pdf, outline_dest_entry['D'])
                    outline_dest = {
                        'page': explict_dest[0],
                        'rect_X': explict_dest[1],
                        'rect_Y': explict_dest[2],
                    }
                    title_bytes = outline_obj['Title']
                else:
                    raise RuntimeError(
                        f"Page {outline_dest_entry['D'][0]} is not an indirect reference to a page object",
                    )
            else:
                # named destination
                if isinstance(outline_dest_entry['D'], PSLiteral):
                    # PDF 1.1 name object
                    outline_dest = outline_dest_entry['D'].name
                else:
                    # PDF 1.2 byte string
                    outline_dest = outline_dest_entry['D'].decode('utf-8')

                if isinstance(outline_obj['Title'], PDFObjRef):
                    title_bytes = outline_obj['Title'].resolve()  # title is a PDFObjRef
                else:
                    title_bytes = outline_obj['Title']
        else:
            # not go-to action, no destination in this document to jump to
            outline_dest = None
            title_bytes = outline_obj['Title']
            LOG.info('Jump target of outline entry "%s" is outside of this document.', outline_obj)
    elif 'Dest' in outline_obj:
        # direct destination, used to directly address page locations
        if isinstance(outline_obj['Dest'], list):
            # explict destination
            if isinstance(outline_obj['Dest'][0], PDFObjRef):
                explict_dest = get_explict_dest(pdf, outline_obj['Dest'])
                outline_dest = {
                    'page': explict_dest[0],
                    'rect_X': explict_dest[1],
                    'rect_Y': explict_dest[2],
                }
            else:
                raise RuntimeError(f"Page {outline_obj['Dest'][0]} is not an indirect reference to a page object")
        else:
            # named destination
            if isinstance(outline_obj['Dest'], PSLiteral):
                # PDF 1.1 name object
                outline_dest = outline_obj['Dest'].name
            else:
                # PDF 1.2 byte string
                outline_dest = outline_obj['Dest'].decode('utf-8')
        title_bytes = outline_obj['Title']
    else:
        raise ValueError('No key A and Dest in outline.')

    # various encodings like UTF-8 and UTF-16 are in the wild for the title, so using chardet to guess them
    title_decoded = decode_title(title_bytes)

    # check if outline_dest exists
    if outline_dest:
        # get outline_dest location and page number and store in temp_dict
        if des_dict is not None and not isinstance(outline_dest, dict) and des_dict[outline_dest]:
            # outline with named destination, which means outline_dest must not be dict, representing explict
            # destination
            outline = {
                'number': '',
                'title': title_decoded,
                'position': {
                    # TODO change to x, y and give them meaning when comparing to libpdf elements
                    'x0': des_dict[outline_dest]['X'],
                    'y1': des_dict[outline_dest]['Y'],  # dest (X, Y) is left top, equals (x0, y1) in pdfminer
                    'page': des_dict[outline_dest]['Num'],
                },
                'content': [],
            }
        else:
            # outline with explict destination
            outline = {
                'number': '',
                'title': title_decoded,
                'position': {
                    'x0': outline_dest['rect_X'],
                    'y1': outline_dest['rect_Y'],  # dest (X, Y) is left top, equals (x0, y1) in pdfminer
                    'page': outline_dest['page'],
                },
                'content': [],
            }
        outline_list.append(outline)

    if 'First' in outline_obj:
        resolve_outline(outline_obj['First'].resolve(), outline_list[len(outline_list) - 1]['content'], des_dict, pdf)
    if 'Next' in outline_obj:
        resolve_outline(outline_obj['Next'].resolve(), outline_list, des_dict, pdf)


def get_explict_dest(pdf, dest_list):
    """
    Find explict destination page number and rectangle.

    :param pdf: pdfplumber.pdf.PDF object
    :param dest_list: A explict destination list, e.g. [page, /XYZ, left, top, zoom]
    :return: A list of destination contains page number and rectangle coordinates
    """
    dest_page_num = None
    # find page number from page id
    dest_page_id = dest_list[0].objid
    for page in pdf.pages:
        if dest_page_id == page.page_obj.pageid:
            dest_page_num = page.page_number

    # explict destination support a lot possibilities to describe like [page, /XYZ, left, top, zoom], or [page, /Fit]
    # according to TABLE 8.2 Destination syntax of PDF Reference 1.7
    if dest_list[1].name == 'XYZ':
        dest_rect_x = dest_list[2]
        dest_rect_y = dest_list[3]
    else:
        dest_rect_x = 0
        dest_rect_y = dest_list[0].resolve()['MediaBox'][3]  # page top

    return [dest_page_num, dest_rect_x, dest_rect_y]


def update_ann_info(annotation_page_map, ann_resolved, page, idx_page, pdf):  # pylint: disable=too-many-branches
    """
    Fetch the name of annotation, annotation location on the page and destination of the link annotation.

    For link annotation, there are two ways to specify destinations, directly or indirectly. Indirectly means using
    go-to action, annotation['A']['D'], which represent the destination to jump to. Directly means
    annotation['Dest'], which represent the destination of annotation.

    However, annotation['A'] and annotation['Dest'] can't coexist.

    :param annotation_page_map: annotation dictionary mapped to page
    :param ann_resolved: resolved annotation on current page
    :param page: current page
    :param idx_page: index of page
    :param pdf: pdfplumber.pdf.PDF object
    :return: None
    """
    # safety check
    if 'Rect' not in ann_resolved:
        LOG.error('"Rect" is missing in annotation.')

    if 'A' in ann_resolved and 'Dest' in ann_resolved:
        LOG.error('Key A and Dest can not coexist in annotation.')

    # get annotation location on the page
    # Rect[0] is the x0 in pdfminer coordination
    # Rect[1] is the y0 in pdfminer
    # Rect[2] is the x1 in pdfminer
    # Rect[3] is the y1 in pdfminer
    ann_bbox = to_pdfplumber_bbox(
        float(ann_resolved['Rect'][0]) - ANNO_X_TOLERANCE,
        float(ann_resolved['Rect'][1]) - ANNO_Y_TOLERANCE,
        float(ann_resolved['Rect'][2]) + ANNO_X_TOLERANCE,
        float(ann_resolved['Rect'][3]) + ANNO_Y_TOLERANCE,
        page.height,
    )

    left, top, right, bottom = ann_bbox
    if top > bottom:
        LOG.debug(f"invalid annotation bbox: {ann_resolved['Rect']}, {ann_bbox}")
        return
        # maybe continue with swapped bbox
        # ann_bbox = [left, bottom, right, top]

    page_crop = page.within_bbox(ann_bbox)
    ann_text = page_crop.extract_text(x_tolerance=float(1), y_tolerance=float(4))

    if 'A' in ann_resolved:
        # make sure ann_resolved['A'] is resolved
        if isinstance(ann_resolved['A'], PDFObjRef):
            ann_resolved_entry = ann_resolved['A'].resolve()
        else:
            ann_resolved_entry = ann_resolved['A']

        # consider only go-to action
        if ann_resolved_entry['S'].name == 'GoTo':
            if isinstance(ann_resolved_entry['D'], list):
                # explict destination, ann_resolved['A']['D'] is a list
                if isinstance(ann_resolved_entry['D'][0], PDFObjRef):
                    explict_dest = get_explict_dest(pdf, ann_resolved_entry['D'])
                    annotation_page_map[idx_page + 1]['annotation'].append(
                        {
                            'text': ann_text,
                            'rect': ann_resolved['Rect'],
                            'dest': {'page': explict_dest[0], 'rect_X': explict_dest[1], 'rect_Y': explict_dest[2]},
                        },
                    )
                else:
                    raise RuntimeError(
                        f"Page {ann_resolved_entry['D'][0]} is not an indirect reference to a page object",
                    )
            else:
                # Named destination
                if isinstance(ann_resolved_entry['D'], PSLiteral):
                    # PDF 1.1 name object
                    des_name = ann_resolved_entry['D'].name
                else:
                    # PDF 1.2 byte string
                    des_name = ann_resolved_entry['D'].decode('utf-8')
                annotation_page_map[idx_page + 1]['annotation'].append(
                    {
                        'text': ann_text,
                        'rect': ann_resolved['Rect'],
                        'des_name': des_name,
                    },
                )
        else:
            LOG.info(
                'The %s link target on page %s is not in this document.',
                ann_resolved_entry['S'].name,
                idx_page + 1,
            )
    elif 'Dest' in ann_resolved:
        # direct destination, used to directly address page locations
        if isinstance(ann_resolved['Dest'], list):
            # explict destination
            if isinstance(ann_resolved['Dest'][0], PDFObjRef):
                explict_dest = get_explict_dest(pdf, ann_resolved['Dest'])
                anno_dest = {
                    'page': explict_dest[0],
                    'rect_X': explict_dest[1],
                    'rect_Y': explict_dest[2],
                }
                annotation_page_map[idx_page + 1]['annotation'].append(
                    {'text': ann_text, 'rect': ann_resolved['Rect'], 'dest': anno_dest},
                )
            else:
                raise RuntimeError(f"Page {ann_resolved['Dest'][0]} is not an indirect reference to a page object")
        else:
            # Named destination
            if isinstance(ann_resolved['Dest'], PSLiteral):
                # PDF 1.1 name object
                des_name = ann_resolved['Dest'].name
            else:
                # PDF 1.2 byte string
                des_name = ann_resolved['Dest'].decode('utf-8')

            annotation_page_map[idx_page + 1]['annotation'].append(
                {'text': ann_text, 'rect': ann_resolved['Rect'], 'des_name': des_name},
            )
    else:
        raise Exception('Key "A" and "Dest" do not exist in annotations.')


def annotation_dict_extraction(pdf):
    """Extract annotation (link source) from the catalog of the PDF.

    The annotation is stored in page.page_obj.annots instead of page.anno or pdf.doc.catalog, if annotations exist in
    the corresponding page.

    Annotations extracted from each page are stored in a dictionary sorted by pages for extract(). The information of
    annotations are:

    -page
    -rect's coordinates (x0, y0, x1, y1) of the annotations
    -destination's name, which is the interface to map with the name destination catalog (target link).

    """
    LOG.info('Catalog extraction: annotations ...')

    annotation_page_map = {}

    for idx_page, page in enumerate(
        tqdm(pdf.pages, desc='###### Extracting annotations', unit='pages', bar_format=bar_format_lvl2()),
    ):
        if logging_needed(idx_page, len(pdf.pages)):
            LOG.debug('Catalog extraction: annotations page %s of %s', idx_page + 1, len(pdf.pages))

        # extract annotations from page_obj.annots, if any exists
        page_obj = page.page_obj
        if page_obj.annots is not None:
            # TODO remove key 'annotation' and refactor relevant code usage
            annotation_page_map.update({idx_page + 1: {'annotation': []}})

            if isinstance(page_obj.annots, PDFObjRef):
                annotations = page_obj.annots.resolve()
            else:
                annotations = page_obj.annots

            for ann in annotations:
                ann_resolved = ann.resolve()
                if ann_resolved['Subtype'].name == 'Link':
                    update_ann_info(annotation_page_map, ann_resolved, page, idx_page, pdf)
            # if no link annotation on this page, remove this page from annotation dictionary
            if not annotation_page_map[idx_page + 1]['annotation']:
                del annotation_page_map[idx_page + 1]

    if not annotation_page_map:
        return None

    return annotation_page_map


def _resolve_pdf_obj_refs(
    object_to_resolve: Union[List, Dict],
    resolved_objects_flat: Dict[int, Any],
    depth=None,
    reason=None,
):  # pylint: disable=too-many-branches, too-many-statements  # warning not fixed due to algorithmic benefits
    """
    Recursively resolve all PDFObjRef and store them in resolved_objects as values where key is objid.

    The function communicates its work by writing to resolved_objects and unresolved_objects.
    The function calls itself (recursive) if resolved PDFObjRef instances contain further lists or dictionaries.

    :param object_to_resolve: the object that shall be resolved, must be either a list or a dictionary
    :param resolved_objects_flat: all resolved PDFObjRef instances until now
    :return: None
    """
    if depth is None:
        depth = [(reason, object_to_resolve)]
    else:
        depth.append((reason, object_to_resolve))
    resolved_dict = {}  # if object_to_resolve is a dict this will contain a resolved version of it
    resolved_list = []  # if object_to_resolve is a list this will contain a resolved version of it
    if isinstance(object_to_resolve, dict):
        for key, value in object_to_resolve.items():
            if isinstance(value, dict):
                # recurse and add child dict
                ret_dict, _ = _resolve_pdf_obj_refs(value, resolved_objects_flat, depth, f'key {key} > dict')
                resolved_dict[key] = ret_dict
            elif isinstance(value, list):
                # recurse and set list
                _, ret_list = _resolve_pdf_obj_refs(value, resolved_objects_flat, depth, f'key {key} > list')
                resolved_dict[key] = ret_list
            elif isinstance(value, PDFObjRef):
                # Parent: used in Page to navigate to Pages
                # Prev: used in Outline to get to previous section
                # Last: used in Outline to get to last section
                # ParentTree: used in StructTreeRoot to get to parent
                # P: used in StructElem to get to parent
                forbidden_keys = ['Parent', 'Prev', 'Last', 'ParentTree', 'P']
                if key in forbidden_keys:
                    # don't resolve PDFObjRef under forbidden keys to avoid endless recursion
                    resolved_dict[key] = value
                else:
                    resolved = value.resolve()
                    if value.objid not in resolved_objects_flat:
                        resolved_objects_flat[value.objid] = resolved
                    if isinstance(resolved, dict):
                        # recurse and add child dict
                        ret_dict, _ = _resolve_pdf_obj_refs(
                            resolved,
                            resolved_objects_flat,
                            depth,
                            f'key {key} > PDFObjRef {value.objid} > dict',
                        )
                        resolved_dict[key] = ret_dict
                    elif isinstance(resolved, list):
                        # recurse and set list
                        _, ret_list = _resolve_pdf_obj_refs(
                            resolved,
                            resolved_objects_flat,
                            depth,
                            f'key {key} > PDFObjRef {value.objid} > list',
                        )
                        resolved_dict[key] = ret_list
                    else:
                        resolved_dict[key] = resolved  # add resolved element to dictionary
            else:
                # leave other types as they are
                resolved_dict[key] = value
    elif isinstance(object_to_resolve, list):
        for idx, value in enumerate(object_to_resolve):
            if isinstance(value, dict):
                ret_dict, _ = _resolve_pdf_obj_refs(value, resolved_objects_flat, depth, f'list idx {idx} > dict')
                resolved_list.append(ret_dict)
            elif isinstance(value, list):
                _, ret_list = _resolve_pdf_obj_refs(value, resolved_objects_flat, depth, f'list idx {idx} > list')
                resolved_list.append(ret_list)
            elif isinstance(value, PDFObjRef):
                resolved = value.resolve()
                if value.objid not in resolved_objects_flat:
                    resolved_objects_flat[value.objid] = resolved
                if isinstance(resolved, dict):
                    # recurse and add child dict
                    ret_dict, _ = _resolve_pdf_obj_refs(
                        resolved,
                        resolved_objects_flat,
                        depth,
                        f'list idx {idx} > PDFObjRef {value.objid} > dict',
                    )
                    resolved_list.append(ret_dict)
                elif isinstance(resolved, list):
                    # recurse and set list
                    _, ret_list = _resolve_pdf_obj_refs(
                        resolved,
                        resolved_objects_flat,
                        depth,
                        f'list idx {idx} > PDFObjRef {value.objid} > list',
                    )
                    resolved_list.append(ret_list)
                else:
                    resolved_list.append(value)
            else:
                # leave other types as they are
                resolved_list.append(value)
    else:
        raise RuntimeError('object_to_resolve must of type dictionary or list')
    del depth[-1]  # pop last item in list
    return resolved_dict, resolved_list


def extract_catalog(pdf, no_annotations: bool):
    """
    Extract catalog document of a PDF.

    According to https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf,
    document catalog contains reference to other objects like outline, named destination, pages.

    Extract outline if exists.
    Extract annotation from pages.
    Extract named destination.

    """
    LOG.info('Catalog extraction started ...')

    # debug purpose only
    # resolved_objects: Dict[int, Any] = {}  # key is the PDFObjRef.objid and value the resolved object
    # resolved_catalog, _ = _resolve_pdf_obj_refs(pdf.doc.catalog, resolved_objects)
    # del resolved_catalog  # denote it is not yet used

    if no_annotations:
        ann_dict = None
        LOG.info('Catalog extraction: annotations is excluded')
    else:
        # extract annotation (link source) and store in the dict by pages for further process of links
        # on texts in extract()
        ann_dict = annotation_dict_extraction(pdf)

    # extract name destination (link target)and store in the dict for further process in extract()
    des_dict = get_named_destination(pdf)

    # extract outline of a pdf, if it exists. All the chapters of outline are in a nested and hierarchical structure
    outline_dict = get_outline(pdf, des_dict)

    catalog['outline'] = outline_dict
    catalog['annos'] = ann_dict
    catalog['dests'] = des_dict
