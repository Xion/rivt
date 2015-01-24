"""
rivt :: Simple image merger
"""
from __future__ import print_function

from collections import Iterable, Sequence
from operator import itemgetter
import sys

from images2gif import images2gif  # GIFception!
from PIL import Image

from rivt.data import Axis


# TODO(xion): split into more modules


__version__ = "0.0.1"
__description__ = "Simple image merger"
__author__ = "Karol Kuczmarski"
__license__ = "GPLv3"



# Main algorithm

def sew(images, axis=Axis.HORIZONTAL):
    """Sews several images together, pasting it into final image side by side.

    :param axis: Axis along which the images should be arranged.

    :return: PIL :class:`Image`, or :class:`Animation`
             (if the result is an animation).
    """
    if len(images) == 1:
        return images[0]

    animations = list(map(Animation, images))
    if all(len(anim) == 1 for anim in animations):
        return sew_static_images(images, axis)
    else:
        return sew_animations(animations, axis)


def sew_static_images(images, axis=Axis.HORIZONTAL):
    """Sews several still images together, pasting it into final image
    side by side, one after another.

    :param axis: Axis along which the images should be arranged.

    :return: PIL :class:`Image`
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

    return result


def sew_animations(animations, axis=Axis.HORIZONTAL):
    """Sew several animations together, arranging it into a final animation
    in a side-by-side fashion.

    :param axis: Axis along which the animations should be arranged.

    :return: :class:`Animation`
    """
    result_frames = []  # list of PIL :class:`Image` objects

    time = 0  # in seconds

    # TODO(xion): extract a namedtuple with AnimationState
    # and keep a single array of that
    time_indices = [0] * len(animations)  # also in seconds
    frame_indices = [0] * len(animations)
    loop_counters = [0] * len(animations)

    # determine the total duration of the resulting animation;
    # finite animations shall be played fully, whereas infinite ones
    # only as few times as necesary for synchronization
    # (within 0.1 second tolerance)
    individual_durations = [
        anim.total_duration if anim.is_finite else anim.animation_duration
        for anim in animations]
    result_duration = reduce(
        lcm, (round(d, 1) * 10 for d in individual_durations)) / 10

    # "play" all the animations simultaneously and create new, sewn frame
    # whenever any of the continuent frames change
    while time < result_duration:
        sewn_frame = sew_static_images(
            [anim[idx] for anim, idx in zip(animations, frame_indices)], axis)
        result_frames.append(sewn_frame)

        # find out what animation should have its frame changed next
        # TODO(xion): if the time increment is very small,
        # elide it, so that we don't produce too many frames with small changes
        next_frame_anim_index, new_time = min(
            ((i, time_index + anim.duration(frame_index))
             for i, (anim, time_index, frame_index) in enumerate(
                zip(animations, time_indices, frame_indices))),
            key=itemgetter(1))

        # advance the time, as counted for this animation and globally
        next_frame_anim = animations[next_frame_anim_index]
        time_indices[next_frame_anim_index] += \
            next_frame_anim.duration(frame_indices[next_frame_anim_index])
        time = new_time

        # advance to a next frame, taking looping into account
        next_frame_index = frame_indices[next_frame_anim_index] + 1
        if next_frame_index >= len(next_frame_anim):
            loop_count = next_frame_anim.loop_count or sys.maxsize
            if loop_counters[next_frame_anim_index] < loop_count:
                loop_counters[next_frame_anim_index] += 1
                next_frame_index %= len(next_frame_anim)
            else:
                next_frame_index -= 1  # reached the end of this animation
        frame_indices[next_frame_anim_index] = next_frame_index

    # (note that ideally, when finite and infinite animations are combined,
    # we'd want to start looping after all the finite ones finish;
    # unfortunately, GIF only supports looping of the whole animation,
    # so the next best thing is to make one infinite animation
    # loop the whole thing)
    result = Animation(result_frames)
    result.loop_count = 1 if all(anim.is_finite for anim in animations) else 0
    return result


def lcm(a, b):
    """Compute the least common multiple of two numbers."""
    product = a * b

    while b:
        a, b = b, a % b
    gcd = a

    return product // gcd


 # Handling animated GIFs

class Animation(Sequence):
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

    @property
    def is_finite(self):
        return (self.loop_count or 0) > 0


def save_gif(fp, frames):
    """Saves animated GIF consisting of given frames.

    :param frames: :class:`Animation` object or iterable of PIL images
    """
    if isinstance(frames, Animation):
        loop_count = frames.loop_count
        frames = list(frames)  # get list of PIL images
    elif isinstance(frames, Iterable):
        loop_count = 0  # indefinitely
    else:
        raise ValueError("invalid frames object of type %r" % type(frames))

    durations = [frame.info['duration'] for frame in frames]

    gif_writer = images2gif.GifWriter()
    gif_writer.transparency = False
    images, _, _ = gif_writer.handleSubRectangles(frames, True)

    frame_dispose = 1  # leave frame in place after it ends
    gif_writer.writeGifToFile(fp, images, durations, loop_count, frame_dispose)
