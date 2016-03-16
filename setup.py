import setuptools
from distutils.core import setup
import os

long_desc = '''\
aenum --- support for advanced enumerations, namedtuples, and constants
===========================================================================

aenum includes the new Python stdlib enum module available in Python 3.4
backported for previous versions of Python from 2.7 and 3.3+
tested on 2.7, and 3.3+


An ``Enum`` is a set of symbolic names (members) bound to unique, constant
values.  Within an enumeration, the members can be compared by identity, and
the enumeration itself can be iterated over.

A ``NamedTuple`` is a class-based, fixed-length tuple with a name for each
possible position accessible using attribute-access notation.

A ``NamedConstant`` is a class whose members cannot be rebound;  it lacks all other
``Enum`` capabilities, however; consequently, it can have duplicate values.
There is also a ``module`` function that can insert the ``NamedConstant`` class
into ``sys.modules`` where it will appear to be a module whose top-level
names cannot be rebound.


Module Contents
---------------

``NamedTuple``
^^^^^^^^^^^^^^
   Base class for ``creating NamedTuples``_, either by subclassing or via it's
   functional API.

``NamedConstant``
^^^^^^^^^^^^^^^^^
   NamedConstant class for creating groups of constants.  These names cannot be rebound
   to other values.

``Enum``
^^^^^^^^
   Base class for creating enumerated constants.  See section ``Enum Functional API``_
   for an alternate construction syntax.

``IntEnum``
^^^^^^^^^^^
   Base class for creating enumerated constants that are also subclasses of ``int``.

``AutoNumberEnum``
^^^^^^^^^^^^^^^^^^
   Derived class that automatically assigns an ``int`` value to each member.

``OrderedEnum``
^^^^^^^^^^^^^^^
   Derived class that adds ``<``, ``<=``, ``>=``, and ``>`` methods to an ``Enum``.

``UniqueEnum``
^^^^^^^^^^^^^^
   Derived class that ensures only one name is bound to any one value.

``unique``
^^^^^^^^^^
   Enum class decorator that ensures only one name is bound to any one value.

``constant``
^^^^^^^^^^^^
   Descriptor to add constant values to an ``Enum``

``convert``
^^^^^^^^^^^
   Helper to transform target global variables into an ``Enum``.

``enum``
^^^^^^^^
   Helper for specifying keyword arguments when creating ``Enum`` members.

``export``
^^^^^^^^^^`
   Helper for inserting ``Enum`` members into a namespace (usually ``globals()``.

``extend_enum``
^^^^^^^^^^^^^^^
   Helper for adding new ``Enum`` members after creation.

``module``
^^^^^^^^^^
   Function to take a ``NamedConstant`` or ``Enum`` class and insert it into
   ``sys.modules`` with the affect of a module whose top-level constant and
   member names cannot be rebound.

``skip``
^^^^^^^^
   Descriptor to add a normal (non-``Enum`` member) attribute to an ``Enum``
   or ``NamedConstant``.


Creating an Enum
----------------

Enumerations can be created using the ``class`` syntax, which makes them
easy to read and write.  To define an enumeration, subclass ``Enum`` as
follows::

    >>> from aenum import Enum
    >>> class Color(Enum):
    ...     red = 1
    ...     green = 2
    ...     blue = 3

The ``Enum`` class is also callable, providing the following functional API::

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

The simple method of creating ``NamedTuples`` requires always specifying all
possible arguments when creating instances; failure to do so will raise
exceptions.

However, it is possible to specify both docstrings and default values when
creating a ``NamedTuple`` using the class method::

    >>> class Point(NamedTuple):
    ...     x = 0, 'horizontal coordinate', 0
    ...     y = 1, 'vertical coordinate', 0
    ...
    >>> Point()
    Point(x=0, y=0)


Creating NamedConstants
------------------

    >>> class K(NamedConstant):
    ...     PI = 3.141596
    ...     TAU = 2 * PI
    ...
    >>> K.TAU
    6.283192
'''

setup(
       name='aenum',
       version='1.3.2',
       url='https://bitbucket.org/stoneleaf/aenum',
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
       description="Advanced Enumerations (compatible with Python's stdlib Enum), NamedTuples, and NamedConstants",
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
