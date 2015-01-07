#!/usr/bin/env python
"""
rivt :: Ludicrously simple image merger
"""
from __future__ import print_function

import argparse
from enum import IntEnum
from itertools import chain
import sys

from PIL import Image


__version__ = "0.0.1"
__description__ = "Ludicrously simple image merger"
__author__ = "Karol Kuczmarski"
__license__ = "GPLv3"


def main(argv=sys.argv):
    args = parse_argv(argv)

    source_images = list(map(Image.open, args.images))
    result_image = sew(source_images, args.axis)

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

    input_group = parser.add_argument_group("Input", "Source images to merge")
    input_group.set_defaults(axis=Axis.HORIZONTAL)
    input_group.add_argument('images', type=str, nargs='+',
                             help="image files to sew together",
                             metavar="IMAGE")
    axis_group = input_group.add_mutually_exclusive_group()
    axis_group.add_argument('--horz', '--horizontal', dest='axis',
                            action='store_const', const=Axis.HORIZONTAL,
                            help="arrange the images horizontally")
    axis_group.add_argument('--vertical', dest='axis',
                            action='store_const', const=Axis.VERTICAL,
                            help="arrange the images vertically")

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

    # get the autogenerated usage string and tweak it a little
    # to exclude the miscellaneous flags which aren't part of a normal usage
    usage = parser.format_usage()
    usage = usage[usage.find(parser.prog):].rstrip("\n")  # remove cruft
    for misc_flag in chain.from_iterable(a.option_strings
                                         for a in misc_group._group_actions):
        usage = usage.replace(" [%s]" % misc_flag, "")
    parser.usage = usage

    return parser.parse_args(argv[1:])


class Axis(IntEnum):
    HORIZONTAL = 0  # X coordinate
    VERTICAL = 1  # Y coordinate


def sew(images, axis=Axis.HORIZONTAL):
    """Sews several images together, pasting it into final image side-by-side.

    :param axis: Axis along which the images should be arranged.

    :return: PIL :class:`Image` or iterable thereof (if result is an animation)
    """
    # 'main' and 'cross' axis are defined analogously like in CSS3 flexbox,
    # assuming that we treat images as the child elements
    main_size = lambda arg: getattr(arg, 'size', arg)[axis]
    cross_size = lambda arg: getattr(arg, 'size', arg)[1 - axis]
    xy_size = lambda main, cross: (main if axis == Axis.HORIZONTAL else cross,
                                   main if axis == Axis.VERTICAL else cross)

    max_cross_size = max(cross_size(img) for img in images)
    adjusted_sizes = [
        xy_size(int(main_size(img) * cross_size(img) / float(max_cross_size)),
                max_cross_size)
        for img in images]
    total_main_size = sum(map(main_size, adjusted_sizes))

    result = Image.new('RGB', xy_size(total_main_size, max_cross_size))

    # TODO(xion): allow to specify resampling filter
    pos = 0
    for image, size in zip(images, adjusted_sizes):
        result.paste(image.resize(size, Image.BILINEAR), xy_size(pos, 0))
        pos += main_size(size)

    # TODO(xion): support sewing animated GIFs
    return result


if __name__ == '__main__':
    sys.exit(main() or 0)
