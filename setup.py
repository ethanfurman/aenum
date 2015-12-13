import os
from distutils.core import setup

long_desc = '''\
`aenum` --- support for advanced enumerations and namedtuples
===============================================================

An enumeration is a set of symbolic names (members) bound to unique, constant
values.  Within an enumeration, the members can be compared by identity, and
the enumeration itself can be iterated over.

A NamedTuple is a class-based, fixed-length tuple with a name for each possible
position accessible using attribute-access notation.


Module Contents
---------------

This module defines five enumeration classes that can be used to define unique
sets of names and values, one `Enum` class decorator, and one named tuple
class

`Enum`

Base class for creating enumerated constants.

`IntEnum`

Base class for creating enumerated constants that are also subclasses of `int`.

`AutoNumberEnum`

Derived class that automatically assigns an `int` value to each member.

`OrderedEnum`

Derived class that adds `<`, `<=`, `>=`, and `>` methods to an `Enum`.

`UniqueEnum`

Derived class that ensures only one name is bound to any one value.

`unique`

Enum class decorator that ensures only one name is bound to any one value.

`NamedTuple`

Base class for creating NamedTuples, either by subclassing or via it's
functional API.


Creating an Enum
----------------

Enumerations can be created using the `class` syntax, which makes them
easy to read and write.  To define an enumeration, subclass `Enum` as
follows::

    >>> from aenum import Enum
    >>> class Color(Enum):
    ...     red = 1
    ...     green = 2
    ...     blue = 3

The `Enum` class is also callable, providing the following functional API::

    >>> Animal = Enum('Animal', 'ant bee cat dog')
    >>> Animal
    <enum 'Animal'>
    >>> Animal.ant
    <Animal.ant: 1>
    >>> Animal.ant.value
    1
    >>> list(Animal)
    [<Animal.ant: 1>, <Animal.bee: 2>, <Animal.cat: 3>, <Animal.dog: 4>]


Creating NamedTuples
--------------------

Simple
^^^^^^

The most common way to create a new NamedTuple will be via the functional API::

    >>> from aenum import NamedTuple
    >>> Book = NamedTuple('Book', 'title author genre', module=__name__)

Advanced
^^^^^^^^

The simple method of creating `NamedTuples` requires always specifying all
possible arguments when creating instances; failure to do so will raise
exceptions.

However, it is possible to specify both docstrings and default values when
creating a `NamedTuple` using the class method::

    >>> class Point(NamedTuple):
    ...     x = 0, 'horizontal coordinate', 0
    ...     y = 1, 'vertical coordinate', 0
    ...
    >>> Point()
    Point(x=0, y=0)
'''

setup( name='aenum',
       version='1.2.1',
       url='https://pypi.python.org/pypi/aenum',
       packages=['aenum'],
       package_data={
           'aenum' : [
               'LICENSE',
               'README',
               'doc/aenum.rst',
               'doc/aenum.pdf',
               ]
           },
       license='BSD License',
       description="Advanced Enumerations (compatible with Python's stdlib Enum) and NamedTuples",
       long_description=long_desc,
       provides=['aenum'],
       author='Ethan Furman',
       author_email='ethan@stoneleaf.us',
       classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Topic :: Software Development',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            ],
    )
