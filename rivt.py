#!/usr/bin/env python
"""
rivt :: Ludicrously simple image merger
"""
from __future__ import print_function

import argparse
from collections import Iterable, Sequence
from enum import IntEnum
from itertools import chain
import sys

from images2gif import GifWriter
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
        # and/or, more importantly, the extension of output file
        result_image.save(args.output, 'PNG')


def parse_argv(argv):
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)

    # TODO(xion): support URLs as IMAGE arguments
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


# Main algorithm

class Axis(IntEnum):
    HORIZONTAL = 0  # X coordinate
    VERTICAL = 1  # Y coordinate


def sew(images, axis=Axis.HORIZONTAL):
    """Sews several images together, pasting it into final image side-by-side.

    :param axis: Axis along which the images should be arranged.

    :return: PIL :class:`Image` or iterable thereof (if result is an animation)
    """
    # 'main' and 'cross' axis are defined analogously to CSS3 flexbox,
    # assuming that we treat images as children of an element with display:flex
    main_size = lambda arg: getattr(arg, 'size', arg)[axis]
    cross_size = lambda arg: getattr(arg, 'size', arg)[1 - axis]
    xy_size = lambda main, cross: (main if axis == Axis.HORIZONTAL else cross,
                                   main if axis == Axis.VERTICAL else cross)

    # rescale images to fit the smallest one (as per its cross size)
    min_cross_size = min(cross_size(img) for img in images)
    adjusted_sizes = [
        xy_size(int(main_size(img) * float(min_cross_size) / cross_size(img)),
                min_cross_size)
        for img in images]
    total_main_size = sum(map(main_size, adjusted_sizes))

    result = Image.new('RGB', xy_size(total_main_size, min_cross_size))

    # TODO(xion): allow to specify resampling filter
    pos = 0
    for image, size in zip(images, adjusted_sizes):
        result.paste(image.resize(size, Image.BILINEAR), xy_size(pos, 0))
        pos += main_size(size)

    # TODO(xion): support sewing animated GIFs
    return result


 # Handling animation

class Frames(Sequence):
    """Object holding individual frames of a GIF animated image.

    :param image: PIL :class:`Image` to read the frames from,
                  or an image for the first frame

    Further positional arguments are optional additional images
    to put into the frame
    """
    def __init__(self, image, **more):
        frames = []

        if more:
            frames.append(image)
            frames.extend(more)
        else:
            while True:
                frames.append(image.copy())
                try:
                    image.seek(image.tell() + 1)
                except EOFError:
                    break

        self._frames = frames

    def __getitem__(self, idx):
        return self._frames[idx]

    def __len__(self):
        return len(self._frames)

    def duration(self, frame, value=None):
        """Returns duration of a frame in seconds, if known,
        or sets it to given value.
        """
        if isinstance(frame, int):
            frame = self._frames[frame]

        if value is None:
            if 'duration' in frame.info:
                return int(frame.info['duration']) / 1000.0
        else:
            frame.info['duration'] = value * 1000

    @property
    def durations(self):
        """Iterable of all frame durations."""
        return map(self.duration, self._frames)

    @property
    def animation_duration(self):
        """Duration of a single playback of the animation."""
        return sum(self.durations) \
            if all(d is not None for d in self.durations) \
            else None

    @property
    def loop_count(self):
        """Animation loop count.

        1 means no looping (play once). 0 means repeat indefinitely.
        ``None`` means unknown or not available.
        """
        return self._frames[0].info.get('loop', None)

    @loop_count.setter
    def loop_count(self, value):
        self._frames[0].info['loop'] = value

    @property
    def total_duration(self):
        """Total duration of the animation, including looping."""
        d = self.animation_duration
        if d is None or self.loop_count is None:
            return None
        return float('inf') if self.loop_count == 0 else d * self.loop_count


def save_gif(fp, frames):
    """Saves animated GIF consisting of given frames.

    :param frames: :class:`Frames` object or iterable of PIL images
    """
    if isinstance(frames, Frames):
        loop_count = frames.loop_count
        frames = list(frames)  # get list of PIL images
    elif isinstance(frames, Iterable):
        loop_count = 0  # indefinitely
    else:
        raise ValueError("invalid frames object of type %r" % type(frame))

    durations = [frame.info['duration'] for frame in frames]

    gif_writer = GifWriter()
    gif_writer.transparency = False
    images, _, _ = gif_writer.handleSubRectangles(frames, True)

    frame_dispose = 1  # leave frame in place after it ends
    gif_writer.writeGifToFile(fp, images, durations, loop_count, frame_dispose)


if __name__ == '__main__':
    sys.exit(main() or 0)
