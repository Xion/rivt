"""
Module with data definitions used throughout the program.
"""
from enum import IntEnum


__all__ = ['Axis']


class Axis(IntEnum):
    """Enum representing one of the two axes along which
    images can be sewn together.
    """
    #: Horizontal axis.
    #: Enum value corresponds to X coordinate of an (x, y) tuple.
    HORIZONTAL = 0

    #: Vertical axis.
    #: Enum value corresponds to Y coordinate of an (x, y) tuple.
    VERTICAL = 1
