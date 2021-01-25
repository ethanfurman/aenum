try:
    import setuptools
except ImportError:
    pass
from distutils.core import setup
import sys

long_desc = '''\
Advanced Enumerations (compatible with Python's stdlib Enum), NamedTuples, and NamedConstants

aenum includes a Python stdlib Enum-compatible data type, as well as a metaclass-based NamedTuple implementation and a NamedConstant class.

An Enum is a set of symbolic names (members) bound to unique, constant values. Within an enumeration, the members can be compared by identity, and the enumeration itself can be iterated over.  Support exists for unique values, multiple values, auto-numbering, and suspension of aliasing (members with the same value are not identical), plus the ability to have values automatically bound to attributes.

A NamedTuple is a class-based, fixed-length tuple with a name for each possible position accessible using attribute-access notation as well as the standard index notation.

A NamedConstant is a class whose members cannot be rebound; it lacks all other Enum capabilities, however.

Enum classes:

- Enum: Base class for creating enumerated constants.

- IntEnum: Base class for creating enumerated constants that are also
           subclasses of int.

- Flag: Base class for creating enumerated constants that can be combined
        using the bitwise operations without losing their Flag membership.

- IntFlag: Base class for creating enumerated constants that can be combined
           using the bitwise operators without losing their IntFlag membership.
           IntFlag members are also subclasses of int.

- AutoNumberEnum: Derived class that automatically assigns an int value to each
                  member.

- OrderedEnum: Derived class that adds <, <=, >=, and > methods to an Enum.

- UniqueEnum: Derived class that ensures only one name is bound to any one
              value.

Utility functions include:

- convert: helper to convert target global variables into an Enum

- constant: helper class for creating constant members

- enum: helper class for creating members with keywords

- enum_property: property to enable enum members to have same named attributes
                 (e.g. `name` and `value`)

- export: helper to insert Enum members into a namespace (usually globals())

- extend_enum: add new members to enumerations after creation

- module: inserts NamedConstant and Enum classes into sys.modules
          where it will appear to be a module whose top-level names
          cannot be rebound

- skip: class that prevents attributes from being converted to a
        constant or enum member

- unique: decorator that ensures no duplicate members
'''

data = dict(
       name='aenum',
       version='3.0.0',
       url='https://github.com/ethanfurman/aenum',
       packages=['aenum'],
       package_data={
           'aenum' : [
               'LICENSE',
               'README',
               'doc/aenum.rst',
               'doc/aenum.pdf',
               ]
           },
       include_package_data=True,
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
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            ],
    )

py2_only = ()
py3_only = ('aenum/test_v3.py', )
make = [
        'rst2pdf aenum/doc/aenum.rst --output=aenum/doc/aenum.pdf',
        ]

if __name__ == '__main__':
    if 'install' in sys.argv:
        import os, sys
        if sys.version_info[0] != 2:
            for file in py2_only:
                try:
                    os.unlink(file)
                except OSError:
                    pass
        if sys.version_info[0] != 3:
            for file in py3_only:
                try:
                    os.unlink(file)
                except OSError:
                    pass
    setup(**data)
