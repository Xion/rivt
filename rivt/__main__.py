#!/usr/bin/env python
"""
Executable script.
"""
import sys

from PIL import Image

from rivt import sew
from rivt.args import parse_argv


def main(argv=sys.argv):
    args = parse_argv(argv)

    source_images = list(map(Image.open, args.images))
    result_image = sew(source_images, args.axis)

    if args.show:
        result_image.show()
    else:
        # TODO(xion): decide on output format based on input formats
        # and/or, more importantly, the extension of output file
        result_image.save(args.output, 'PNG')


if __name__ == '__main__':
    sys.exit(main() or 0)
