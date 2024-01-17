"""Application entry point."""

import logging
import re
import sys
from typing import List, Optional, Tuple

import click

# not importing load(), so no circular import when importing from root __init__.py
from libpdf import __summary__, __version__, parameters  # pylint: disable=cyclic-import
from libpdf.apiobjects import ApiObjects
from libpdf.extract import LibpdfException, extract
from libpdf.log import config_logger, get_level_name, set_log_level
from libpdf.parameters import RENDER_ELEMENTS
from libpdf.process import output_dump
from libpdf.progress import COLORAMA_AVAILABLE, TQDM_AVAILABLE, bar_format_lvl1, tqdm
from libpdf.utils import visual_debug_libpdf

LOG = logging.getLogger(__name__)


def main(  # pylint: disable=too-many-arguments,too-many-locals  # no reasonable workaround available for API/CLI entry
    pdf: str,
    verbose: int = 0,
    page_range: str = None,
    page_crop: Tuple[float, float, float, float] = None,
    smart_page_crop: bool = False,
    output_format: str = None,
    output_path: str = None,
    save_figures: bool = False,
    figure_dir: str = None,
    no_annotations: bool = False,
    no_chapters: bool = False,
    no_paragraphs: bool = False,
    no_tables: bool = False,
    no_figures: bool = False,
    no_rects: bool = False,
    crop_rects_text: bool = False,
    cli_usage: bool = False,
    visual_debug: bool = False,
    visual_debug_output_dir: str = None,
    visual_split_elements: bool = False,
    visual_debug_include_elements: List[str] = None,
    visual_debug_exclude_elements: List[str] = None,
) -> Optional[ApiObjects]:
    """
    Entry point for both CLI and API.

    :param pdf: path to the PDF to read
    :param verbose: verbosity level as integer (0 = errors, fatal, critical, 1 = warnings, 2 = info, 3 = debug)
    :param page_range: range of pages to extract as string (e.g. 3-5 or 3,4,7 or 3-5,7)
    :param page_crop: Margins for all pages given as space delimited floats in the order top right bottom left.
           The margins will be ignored during extraction, so this can be used to crop all pages.
           The values are given in points (72 points = 1 inch = 25.4 mm). Example: 30 0 45 0
    :param smart_page_crop: flag triggering a smart header/footer detection. The algorithm will get the
           bounding boxes of all paragraphs, tables and figures inside a defined area (given by
           default parameters) at the top/bottom parts of all pages.
           If a certain box is found on multiple pages it is considered a header/footer element and will be
           ignored for the extraction. This feature can be used together with page_crop. In this case the pages will
           first be cropped to the values defined in page_crop and then the header/footer detection will run.
    :param save_figures: flag triggering the export of figures to the figure_dir
    :param figure_dir: output directory for extracted figures; if it does not exist, it will be created
    :param output_format: only relevant for CLI, allowed values are json, yaml or stdout
    :param output_path: only relevant for CLI, path to the output file for output_formats json or yaml
    :param no_annotations: flag triggering the exclusion of annotations from pdf catalog
    :param no_chapters: flag triggering the exclusion of chapters (flat structure of elements)
    :param no_paragraphs: flag triggering the exclusion of paragraphs (no normal text content)
    :param no_tables: flag triggering the exclusion of tables
    :param no_figures: flag triggering the exclusion of figures
    :param no_rects: flag triggering the exclusion of rects
    :param crop_rects_text: flag triggering that rects text should be cropped from text like paragraphs
    :param cli_usage: flag indicating that the function was called through CLI
    :param visual_debug: flag triggering visual debug feature
    :param visual_debug_output_dir: output directory for visualized pdf pages
    :param visual_split_elements: flag triggering split visualized elements in separate folder
    :param visual_debug_include_elements: a list of elements that shall be included when visual debugging
    :param visual_debug_exclude_elements: a list of elements that shall be excluded when visual debugging
    :return: instance of Object class for API usage, None for CLI usage
    """
    if page_crop:
        parameters.PAGE_CROP_MARGINS["top"] = page_crop[0]
        parameters.PAGE_CROP_MARGINS["right"] = page_crop[1]
        parameters.PAGE_CROP_MARGINS["bottom"] = page_crop[2]
        parameters.PAGE_CROP_MARGINS["left"] = page_crop[3]
    if cli_usage:
        LOG.info("libpdf version %s - %s", __version__, __summary__)
    with tqdm(
        total=100,
        desc="### libpdf progress",
        bar_format=bar_format_lvl1(),
        unit="%",
        leave=False,
    ) as overall_pbar:
        pages = None
        if page_range:
            pages = sorted(calculate_pages(page_range))

        if not TQDM_AVAILABLE:
            LOG.warning("Install optional dependency 'tqdm' for progress bars")

        if TQDM_AVAILABLE and not COLORAMA_AVAILABLE:
            LOG.warning(
                "Install optional dependency 'colorama' for colored progress bars"
            )

        LOG.info("Verbosity level: %s", get_level_name(verbose))
        LOG.info("Input file: %s", pdf)
        LOG.info("Output format: %s", output_format)
        if output_path:
            LOG.info("Output path: %s", output_path)
        else:
            LOG.info('Writing extracted data to stdout')
        LOG.info('Page range: [%s]', 'all' if not pages else ','.join(str(x) for x in pages))
        LOG.info('Page crop: %s', 'not cropped' if not page_crop else ' '.join(str(x) for x in page_crop))
        LOG.info('Smart page crop: %s', 'on' if smart_page_crop else 'off')
        LOG.info('Extract annotations: %s', 'no' if no_annotations else 'yes')
        LOG.info('Extract chapters: %s', 'no' if no_chapters else 'yes')
        LOG.info('Extract paragraphs: %s', 'no' if no_paragraphs else 'yes')
        LOG.info('Extract tables: %s', 'no' if no_tables else 'yes')
        LOG.info('Extract figures: %s', 'no' if no_figures else 'yes')
        LOG.info('Extract rects: %s', 'no' if no_rects else 'yes')
        LOG.info('Text rects crop: %s', 'no' if crop_rects_text else 'no')
        overall_pbar.update(1)
        try:
            objects = extract(
                pdf,
                pages,
                smart_page_crop,
                save_figures,
                figure_dir,
                no_annotations,
                no_chapters,
                no_paragraphs,
                no_tables,
                no_figures,
                no_rects,
                crop_rects_text,
                overall_pbar,
            )
        except LibpdfException:
            if cli_usage:
                LOG.critical("Exiting with code 1")
                sys.exit(1)
            else:
                raise

        # visual debug
        if visual_debug:
            visual_debug_libpdf(
                objects,
                visual_debug_output_dir,
                visual_split_elements,
                visual_debug_include_elements,
                visual_debug_exclude_elements,
            )

        if not cli_usage:
            return objects

        LOG.info("Write output...")
        output_dump(output_format, output_path, objects)
        LOG.info("Write output... done")

        overall_pbar.update(7)

    return None


def main_api(  # pylint: disable=too-many-arguments, too-many-locals
    pdf: str,
    verbose: int = 1,  # log level WARNING for library usage is considered a good compromise as a default
    page_range: str = None,
    page_crop: Tuple[float, float, float, float] = None,
    smart_page_crop: bool = False,
    save_figures: bool = False,
    figure_dir: str = "figures",
    no_annotations: bool = False,
    no_chapters: bool = False,
    no_paragraphs: bool = False,
    no_tables: bool = False,
    no_figures: bool = False,
    no_rects: bool = False,
    crop_rects_text: bool = False,
    init_logging: bool = True,
    visual_debug: bool = False,
    visual_debug_output_dir: str = "visual_debug_libpdf",
    visual_split_elements: bool = False,
    visual_debug_include_elements: List[str] = None,
    visual_debug_exclude_elements: List[str] = None,
) -> ApiObjects:
    """
    Entry point for the usage of libpdf as a library.

    The function is actually called ``main_api()`` to better correspond to ``main_cli()`` and ``main()``.
    It is however exposed to the API as ``libpdf.load()`` which is considered more expressive for API users.

    :param pdf: path to the PDF to read
    :param verbose: verbosity level as integer (0 = errors, fatal, critical, 1 = warnings, 2 = info, 3 = debug)
    :param page_range: range of pages to extract as string without spaces (e.g. 3-5 or 3,4,7 or 3-5,7)
    :param page_crop: see description in function core.main()
    :param smart_page_crop: see description in function core.main()
    :param save_figures: flag triggering the export of figures to the figure_dir
    :param figure_dir: output directory for extracted figures; if it does not exist, it will be created
    :param no_annotations: flag triggering the exclusion of annotations from pdf catalog
    :param no_chapters: flag triggering the exclusion of chapters (resulting in a flat list of elements)
    :param no_paragraphs: flag triggering the exclusion of paragraphs (no normal text content)
    :param no_tables: flag triggering the exclusion of tables
    :param no_figures: flag triggering the exclusion of figures
    :param no_rects: flag triggering the exclusion of rects
    :param crop_rects_text: flag triggering that rects text should be cropped from text like paragraphs
    :param init_logging: flag indicating whether libpdf shall instantiate a root log handler that is capable of
                         handling both log messages and progress bars; it does so by passing all log messages to
                         tqdm.write()
    :param visual_debug: flag triggering visual debug feature
    :param visual_debug_output_dir: output directory for visualized pdf pages
    :param visual_split_elements: flag triggering split visualized elements in separate folder
    :param visual_debug_include_elements: a list of elements that shall be included when visual debugging
    :param visual_debug_exclude_elements: a list of elements that shall be excluded when visual debugging
    :return: instance of :class:`~libpdf.apiobjects.ApiObjects` class
    """
    if init_logging:
        config_logger(cli=False)
        set_log_level(verbose)
    # check visual debug include/exclude elements
    if visual_debug:
        if visual_debug_include_elements:
            for visual_incl_element in visual_debug_include_elements:
                if visual_incl_element not in RENDER_ELEMENTS:
                    raise ValueError(
                        f"Given visual included elements {visual_incl_element} not in {RENDER_ELEMENTS}",
                    )
        if visual_debug_exclude_elements:
            for visual_excl_element in visual_debug_exclude_elements:
                if visual_excl_element not in RENDER_ELEMENTS:
                    raise ValueError(
                        f"Given visual excluded elements {visual_excl_element} not in {RENDER_ELEMENTS}",
                    )
        if visual_debug_include_elements and visual_debug_exclude_elements:
            raise ValueError("Can not visual include and exclude at the same time.")

    objects = main(
        pdf,
        verbose=verbose,
        page_range=page_range,
        page_crop=page_crop,
        smart_page_crop=smart_page_crop,
        save_figures=save_figures,
        figure_dir=figure_dir,
        no_annotations=no_annotations,
        no_chapters=no_chapters,
        no_paragraphs=no_paragraphs,
        no_tables=no_tables,
        no_figures=no_figures,
        no_rects = no_rects,
        crop_rects_text = crop_rects_text,
        cli_usage=False,
        visual_debug=visual_debug,
        visual_debug_output_dir=visual_debug_output_dir,
        visual_split_elements=visual_split_elements,
        visual_debug_include_elements=visual_debug_include_elements,
        visual_debug_exclude_elements=visual_debug_exclude_elements,
    )
    return objects


def docstring_parameter(*sub):
    """
    Inject variables into docstrings of functions.

    This is used in below main function to get the version and description
    of the package to the click help screen.
    """

    # decorator definition
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*sub)
        return obj

    return dec


def validate_range(ctx, param, value):
    """Check if the parameter page-range follows the syntax definition."""
    # delete unused parameters to denote they are not used and avoid code checking problems
    del ctx
    del param

    if value is None:
        # this can only happen when the range is not given
        return value
    match = re.match(r"^(\d+-\d+|\d+)(,(\d+-\d+|\d+))*$", value)
    if match is None:
        raise click.BadParameter("must follow the example pattern 2-3,6,8-12")
    numbers = value.replace("-", ",").split(",")
    if not all(int(x) < int(y) for x, y in zip(numbers, numbers[1:])):
        raise click.BadParameter("values must increase monotonic")
    return value


def validate_visual_elements(ctx, param, value):
    """Check if the parameter visual-render-element and visual-not-render-element follows the syntax definition."""
    # delete unused parameters to denote they are not used and avoid code checking problems
    del ctx

    if value is None or len(value) == 0:
        # this can only happen when the value is not given
        return value
    if isinstance(value, tuple):
        # check if multiple options are given, e.g. -ve chapter -ve table
        # TODO check this
        if len(value) > 1:
            raise click.BadParameter(
                "Option cannot be given multiple times. Use comma separation instead."
            )
        value = value[0]

    elements = value.split(",")
    if len(elements) != len(set(elements)):
        raise click.BadParameter(f"Option {param.name} contains duplicate entries.")
    for element in elements:
        if element not in RENDER_ELEMENTS:
            raise click.BadParameter(
                f"Option {param.name} contains an unknown entry '{element}'."
            )
    if param.name == "visual_debug_exclude_elements":
        if len(elements) == len(RENDER_ELEMENTS):
            # TODO Why is this not supported? It will just save the pages as images which might also be useful.
            raise click.BadParameter(
                "Cannot exclude all elements from visual debugging."
            )

    return elements


class DependentOption(click.Option):
    """
    Click option that has dependencies to other options.

    The class supports the following usecases which may also co-exist for a single option:

    1. An option depends on the existence of one or more other options.
    2. An option is mutually exclusive wiht one or more other options.
    """

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        self.depends_on = set(kwargs.pop("depends_on", []))
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))

        help_msgs = []
        if self.depends_on:
            help_msgs.append(f"this option depends on [{', '.join(self.depends_on)}]")
        if self.mutually_exclusive:
            help_msgs.append(
                f"this option is mutually exclusive with [{', '.join(self.mutually_exclusive)}]"
            )
        kwargs["help"] = kwargs.get("help", "") + (f' NOTE: {"; ".join(help_msgs)}')
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        """Handle parse result."""
        if (not self.depends_on.intersection(opts)) and self.name in opts:
            raise click.UsageError(
                f"Illegal usage: '{self.name}' depends on '{', '.join(self.depends_on)}' which is not given.",
            )
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise click.UsageError(
                f"Illegal usage: '{self.name}' is mutually exclusive with '{', '.join(self.mutually_exclusive)}' "
                "which is also given.",
            )

        return super().handle_parse_result(ctx, opts, args)


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True
)
@click.argument(
    "pdf",
    required=True,
    type=click.Path(
        exists=True, readable=True, resolve_path=True, file_okay=True, dir_okay=False
    ),
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="""Verbosity level, can be passed repeatedly.

         \b
         not given   error
         -v          warning
         -vv         info
         -vvv        debug
         """,
)
@click.option(
    "-p",
    "--page-range",
    callback=validate_range,
    help="Page range to extract. No spaces allowed. Examples: 3-5 or 3,4,7 or 3-5,7",
)
@click.option(
    "-m",
    "--page-crop",
    nargs=4,
    type=float,
    help="Margins for all pages given as space delimited floats in the order top right bottom left."
    " The margins will be ignored during extraction, so this can be used to crop all pages."
    " The values are given in points (72 points = 1 inch = 25.4 mm). Example: 30 0 45 0",
)
@click.option(
    "--smart-page-crop",
    is_flag=True,
    help="Flag enabling a smart header/footer detection. The algorithm will get the"
    " bounding boxes of all paragraphs, tables and figures inside a defined area (given by"
    " default parameters) at the top/bottom parts of all pages."
    " If a certain box is found on multiple pages it is considered a header/footer element and will be"
    " ignored for the extraction. This feature can be used together with --page-crop. In this case the pages will"
    " first be cropped to the values defined in page_margins and then the header/footer detection will run.",
)
@click.option(
    "-f",
    "--output-format",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    default="yaml",
    help="Output format.",
)
@click.option("-o", "--output-path", type=click.Path(file_okay=True, dir_okay=False))
@click.option(
    "-sf",
    "--save-figures",
    is_flag=True,
    show_default=True,
    help="Flag enabling the export of PDF figures into the directory given in --figure-dir."
    " Has no effect if --no-figures is also given.",
)
@click.option(
    "-d",
    "--figure-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default="figures",
    show_default=True,
    help="Output directory for extracted figures; if it does not exist, it will be created",
)
@click.option(
    "--no-annotations",
    is_flag=True,
    show_default=True,
    help="Do not extract annotations from catalog. All PDF-internal links will not be resolved."
    " Chapter detection however will work",
)
@click.option(
    "--no-chapters",
    is_flag=True,
    show_default=True,
    help="Do not extract chapter/outline structure. The list of paragraphs, tables and figures will be flattened.",
)
@click.option(
    "--no-paragraphs",
    is_flag=True,
    show_default=True,
    help="Skip paragraphs. The chapter structure will still be preserved.",
)
@click.option("--no-tables", is_flag=True, help="Skip tables.")
@click.option(
    "--no-figures",
    is_flag=True,
    show_default=True,
    help="Skip figures. Figures will not be part of the output JSON/YAML structures and also not saved if"
    " --save-figures is given.",
)
@click.option("-vd", "--visual-debug", is_flag=True, help="Visual debug libpdf.")
@click.option(
    "-vo",
    "--visual-debug-output-dir",
    cls=DependentOption,
    depends_on=["visual_debug"],
    type=click.Path(file_okay=False, dir_okay=True),
    default="visual_debug_libpdf",
    show_default=True,
    help="Output directory for visualized pdf pages.",
)
@click.option(
    "-vs",
    "--visual-split-elements",
    is_flag=True,
    show_default=True,
    help="Put visual debugging elements into separate directories.",
)
@click.option(
    "-vi",
    "--visual-debug-include-elements",
    cls=DependentOption,
    type=str,
    callback=validate_visual_elements,
    help="Included visualized elements when visual debugging. "
    'No space allowed. Example: "chapter,table" or "paragraph"',
    mutually_exclusive=["visual_debug_exclude_elements"],
    depends_on=["visual_debug"],
    multiple=True,  # this error conditions is handled in the callback
)
@click.option(
    "-ve",
    "--visual-debug-exclude-elements",
    cls=DependentOption,
    type=str,
    callback=validate_visual_elements,
    help='Excluded visualized elements when visual debugging. No space allowed. Example: "chapter,table,paragraph"',
    mutually_exclusive=["visual_debug_include_elements"],
    depends_on=["visual_debug"],
    multiple=True,  # this error conditions is handled in the callback
)
@click.version_option(version=__version__)
@click.help_option("-h", "--help")
@docstring_parameter(__version__, __summary__)
# flake8 ignore of docstring issues D400 (end with period) and D403 (first word capitalized) not reasonable here
# as the docstring is used by click in the CLI help page
def main_cli(**kwargs):
    """
    libpdf version {0}: {1}

    The argument PDF points to the PDF path that shall be extracted.
    """  # noqa: D400
    config_logger(cli=True)
    set_log_level(kwargs["verbose"])  # if not given it's 0 which means log level ERROR
    main(**kwargs, cli_usage=True)


def calculate_pages(page_range_string) -> List[int]:
    """
    Calculate a list of pages from the ranges given as CLI parameter page-range.

    :param page_range_string: CLI parameter page-range
    :return: list of pages in given range
    """
    page_ranges = page_range_string.split(",")
    pages = []
    for page_range in page_ranges:
        if "-" in page_range:
            start_page = int(page_range.split("-")[0])
            end_page = int(page_range.split("-")[1])
        else:
            start_page = int(page_range)
            end_page = int(page_range)
        pages.extend(list(range(start_page, end_page + 1)))
    return pages
