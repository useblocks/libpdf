"""Example for imaging that avoids ImageMagick/Wand."""

import datetime
import os

from PIL import Image, ImageDraw

from poppler import PageRenderer, load_from_file
from poppler.cpp.image import format_enum as ImageFormat  # pylint: disable=no-name-in-module

from tests.conftest import PDF_FULL_FEATURES as TEST_PDF

pdf_document = load_from_file(TEST_PDF)

time = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
os.makedirs(f'poppler_pillow/{time}')

COLOR = (255, 0, 0)  # Red
TRANSPARENCY = 0.25  # Degree of transparency, 0-100%
OPACITY = int(255 * TRANSPARENCY)

for idx in range(1, 4):
    # poppler
    page = pdf_document.create_page(idx)
    renderer = PageRenderer()
    renderer.image_format = ImageFormat.argb32  # rgb 32 bit with alpha channel
    image = renderer.render_page(page, xres=600, yres=600)  # resolution affects rendering time

    # Pillow
    im = Image.frombytes('RGBA', (image.width, image.height), image.data, 'raw', str(image.format))

    overlay = Image.new('RGBA', im.size, COLOR + (0,))  # create overlay on top of PDF image
    draw = ImageDraw.Draw(overlay)  # create a context for drawing things on it
    draw.rectangle((400, 225, 700, 700), fill=COLOR + (OPACITY,))  # draw a rectangle
    im = Image.alpha_composite(im, overlay)  # mix the alpha channels
    im = im.convert('RGB')  # Remove alpha for saving in jpg format.
    im = im.crop((100, 100, 2000, 2500))  # crop the image
    with open(f'poppler_pillow/{time}/{idx}_pillow.png', 'wb') as f:
        im.save(f, format='png')

    image.save(f'poppler_pillow/{time}/{idx}_poppler.png', 'png')  # save original poppler image (without drawing)
