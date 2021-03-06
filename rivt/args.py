"""
Module for dealing with the command line arguments.
"""
import argparse
from itertools import chain

from rivt import __description__, __version__
from rivt.data import Axis


__all__ = ['parse_argv']


def parse_argv(argv):
    """Parse command line arguments.

    :param argv: List of command line argument strings,
                 *including* the program name in argv[0]

    :return: Parse result from :func:`argparse.ArgumentParser.parse_args`
    """
    parser = create_argv_parser()
    return parser.parse_args(argv[1:])


# Creating argument parser

def create_argv_parser():
    """Create a :class:`argparse.ArgumentParser` object
    for parsing command line arguments passed by the user.
    """
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)

    add_input_group(parser)
    add_result_group(parser)

    misc_group = add_misc_group(parser)

    # get the autogenerated usage string and tweak it a little
    # to exclude the miscellaneous flags which aren't part of a normal usage
    usage = parser.format_usage()
    usage = usage[usage.find(parser.prog):].rstrip("\n")  # remove cruft
    for misc_flag in chain.from_iterable(a.option_strings
                                         for a in misc_group._group_actions):
        usage = usage.replace(" [%s]" % misc_flag, "")
    parser.usage = usage

    return parser


def add_input_group(parser):
    """Include an argument group that allows to specify the input files.
    :param parser: :class:`argparse.ArgumentParser`
    :return: Resulting argument group
    """
    group = parser.add_argument_group("Input", "Source images to merge")

    # TODO(xion): support URLs as IMAGE arguments
    group.add_argument('images', type=str, nargs='+',
                       help="image files to sew together",
                       metavar="IMAGE")

    axis_group = group.add_mutually_exclusive_group()
    group.set_defaults(axis=Axis.HORIZONTAL)
    axis_group.add_argument('--horz', '--horizontal', dest='axis',
                            action='store_const', const=Axis.HORIZONTAL,
                            help="arrange the images horizontally")
    axis_group.add_argument('--vertical', dest='axis',
                            action='store_const', const=Axis.VERTICAL,
                            help="arrange the images vertically")

    return group


def add_result_group(parser):
    """Include an argument group that allows to specify what to do
    with the result of image merging.

    :param parser: :class:`argparse.ArgumentParser`
    :return: Resulting argument group
    """
    group = parser \
        .add_argument_group("Result", "What to do with resulting image") \
        .add_mutually_exclusive_group()

    group.add_argument('-o', '--output',
                       type=argparse.FileType('wb', 0), default='-',
                       help="output the image to file with given name",
                       metavar="OUTPUT")
    group.add_argument('-s', '--show',
                       action='store_true', default=False,
                       help="show the resulting image "
                            "(in a system-specific way)")

    return group


def add_misc_group(parser):
    """Include the argument group with miscellaneous options.
    :param parser: :class:`argparse.ArgumentParser`
    :return: Resulting argument group
    """
    group = parser.add_argument_group("Miscellaneous", "Other options")

    group.add_argument('--version', action='version', version=__version__)
    group.add_argument('-h', '--help', action='help',
                       help="show this help message and exit")

    return group
