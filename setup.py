#!/usr/bin/env python
"""
rivt
====

{description}
"""
import ast
import os
from setuptools import find_packages, setup
import sys


# Utility functions

def read_tags(filename):
    """Reads values of "magic tags" defined in the given Python file.

    :param filename: Python filename to read the tags from
    :return: Dictionary of tags
    """
    with open(filename) as f:
        ast_tree = ast.parse(f.read(), filename)

    res = {}
    for node in ast.walk(ast_tree):
        if type(node) is not ast.Assign:
            continue

        target = node.targets[0]
        if type(target) is not ast.Name:
            continue

        if not (target.id.startswith('__') and target.id.endswith('__')):
            continue

        name = target.id[2:-2]
        res[name] = ast.literal_eval(node.value)

    return res


def read_requirements(filename='requirements.txt'):
    """Reads the list of requirements from given file.

    :param filename: Filename to read the requirements from.
                     Uses ``'requirements.txt'`` by default.

    :return: Requirements as list of strings
    """
    # allow for some leeway with the argument
    if not filename.startswith('requirements'):
        filename = 'requirements-' + filename
    if not os.path.splitext(filename)[1]:
        filename += '.txt'  # no extension, add default

    def valid_line(line):
        line = line.strip()
        return line and not any(line.startswith(p) for p in ('#', '-'))

    def extract_requirement(line):
        egg_eq = '#egg='
        if egg_eq in line:
            _, requirement = line.split(egg_eq, 1)
            return requirement
        return line

    with open(filename) as f:
        lines = f.readlines()
        return list(map(extract_requirement, filter(valid_line, lines)))


# setup() call

install_requires = read_requirements()
if sys.version_info < (3, 4):
    install_requires.extend(read_requirements('py33'))

tags = read_tags(os.path.join('rivt', '__init__.py'))
__doc__ = __doc__.format(**tags)

setup(
    name='rivt',
    version=tags['version'],
    description=tags['description'],
    long_description=__doc__,
    author=tags['author'],
    url="http://github.com/Xion/rivt",
    license=tags['license'],

    platforms='posix',
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Topic :: Utilities",
    ],

    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': ['rivt=rivt.__main__:main'],
    },

    install_requires=install_requires,
)
