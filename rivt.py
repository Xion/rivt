#!/usr/bin/env python
"""
rivt :: Ludicrously simple image sewer
"""
from __future__ import print_function

import argparse
import sys

from PIL import Image


__version__ = "0.0.1"
__description__ = "Ludicrously simple image sewer"
__author__ = "Karol Kuczmarski"
__license__ = "GPLv3"


def main(argv=sys.argv):
    args = parse_argv(argv)

    source_images = list(map(Image.open, args.images))
    result_image = sew(source_images)

    if args.show:
        result_image.show()
    else:
        # TODO(xion): decide on output format based on input formats
        result_image.save(args.output, 'PNG')


def parse_argv(argv):
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)

    parser.add_argument('images', type=str, nargs='+',
                        help="image files to sew together",
                        metavar="IMAGE")

    result_group = parser.add_argument_group(
        "Result", "What to do with resulting image") \
        .add_mutually_exclusive_group()
    result_group.add_argument('-o', '--output',
                              type=argparse.FileType('wb', 0), default='-',
                              help="output the image to file with given name",
                              metavar="OUTPUT")
    result_group.add_argument('-s', '--show',
                              action='store_true', default=False,
                              help="show the resulting image "
                                   "(in a system-specific way)")

    misc_group = parser.add_argument_group("Miscellaneous", "Other options")
    misc_group.add_argument('--version', action='version', version=__version__)
    misc_group.add_argument('-h', '--help', action='help',
                             help="show this help message and exit")

    return parser.parse_args(argv[1:])


def sew(images):
    max_height = max(img.size[1] for img in images)
    adjusted_sizes = [
        (int(img.size[0] * (img.size[1] / float(max_height))), max_height)
        for img in images]
    total_width = sum(width for width, _ in adjusted_sizes)

    result = Image.new('RGB', (total_width, max_height))

    # TODO(xion): allow to specify resampling filter
    x = 0
    for i, (image, size) in enumerate(zip(images, adjusted_sizes)):
        result.paste(image.resize(size, Image.BILINEAR), (x, 0))
        x += size[0]

    return result


if __name__ == '__main__':
    sys.exit(main() or 0)
