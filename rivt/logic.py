"""
Module with main application's logic.
"""
from operator import itemgetter
import sys

from PIL import Image

from rivt.data import Axis
from rivt.util.gif import Animation


__all__ = ['sew']


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


# Sewing algorithms

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


# Utility functions

def lcm(a, b):
    """Compute the least common multiple of two numbers."""
    product = a * b

    while b:
        a, b = b, a % b
    gcd = a

    return product // gcd
