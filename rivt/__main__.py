#!/usr/bin/env python
"""
Executable script.
"""
from __future__ import print_function

from distutils.spawn import find_executable
import os
import sys

import envoy
from PIL import Image
import six

from rivt.args import parse_argv
from rivt.logic import sew


__all__ = ['main']


def main(argv=sys.argv):
    """Entry point."""
    args = parse_argv(argv)

    source_images = list(map(Image.open, args.images))
    result_image = sew(source_images, args.axis)

    if args.show:
        return show_image(result_image)
    else:
        # TODO(xion): decide on output format based on input formats
        # and/or, more importantly, the extension of output file
        result_image.save(args.output, 'PNG')


def show_image(image):
    """Show given image to the user, if possible.
    :param image: PIL :class:`Image` object
    """
    # use PIL's Image.show() only if it will actually do anything
    is_posix = os.name == 'posix'
    is_osx =  sys.platform == 'darwin'
    if not is_posix or is_osx or find_executable('xv'):
        return image.show()

    # use `display` binary from ImageMagick if available
    if find_executable('display'):
        image_data = six.StringIO()
        image.save(image_data, 'PNG') ; image_data.seek(0)
        return envoy.run('display -', data=image_data).status_code

    # TODO(xion): devise more alternatives; some possible options:
    # * `eog` on a temporary file
    print("can't show resulting image without `xv` or `display` binaries",
          file=sys.stdout)
    return -1


if __name__ == '__main__':
    sys.exit(main() or 0)
