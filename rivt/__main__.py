#!/usr/bin/env python
"""
Executable script.
"""
from __future__ import print_function

from distutils.spawn import find_executable
import os
import sys

from PIL import Image

from rivt.args import parse_argv
from rivt.logic import sew


__all__ = ['main']


def main(argv=sys.argv):
    """Entry point."""
    args = parse_argv(argv)

    source_images = list(map(Image.open, args.images))
    result_image = sew(source_images, args.axis)

    if args.show:
        show_image(result_image)
    else:
        # TODO(xion): decide on output format based on input formats
        # and/or, more importantly, the extension of output file
        result_image.save(args.output, 'PNG')


def show_image(image):
    """Show given image to the user, if possible.
    :param image: PIL :class:`Image` object
    """
    # check if PIL's Image.show() will actually do anything
    non_osx_unix = os.name == 'posix' and sys.platform != 'darwin'
    if non_osx_unix:
        xv_exists = find_executable('xv') is not None
        if not xv_exists:
            # TODO(xion): devise an alternative; some possible options:
            # * `display` from Imagemagick
            # * `eog` on a temporary file
            print("xv not found, can't show resulting image", file=sys.stdout)
            return

    image.show()


if __name__ == '__main__':
    sys.exit(main() or 0)
