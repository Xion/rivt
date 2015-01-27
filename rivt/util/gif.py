"""
Module for handling animated GIFs.
"""
from collections import Iterable, Sequence

from images2gif import images2gif  # GIFception!


__all__ = ['Animation', 'save_gif']


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
