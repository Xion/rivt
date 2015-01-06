#!/usr/bin/env python
"""
rivt :: Ludicrously simple image sewer
"""
from __future__ import print_function

import argparse
import sys


__version__ = "0.0.1"
__description__ = "Ludicrously simple image sewer"
__author__ = "Karol Kuczmarski"
__license__ = "GPLv3"


def main(argv=sys.argv):
    args = parse_argv(argv)


def parse_argv(argv):
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)

    misc_group = parser.add_argument_group("Miscellaneous", "Other options")
    misc_group.add_argument('--version', action='version', version=__version__)
    misc_group.add_argument('-h', '--help', action='help',
                             help="show this help message and exit")

    return parser.parse_args(argv[1:])


if __name__ == '__main__':
    sys.exit(main() or 0)
