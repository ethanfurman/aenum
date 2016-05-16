try:
    import setuptools
except ImportError:
    pass
from distutils.core import setup
import sys

long_desc = '''\
Advanced Enumerations (compatible with Python's stdlib Enum), NamedTuples, and NamedConstants

aenum includes a Python stdlib Enum-compatible data type, as well as a metaclass-based NamedTuple implementation and a NamedConstant class.

An Enum is a set of symbolic names (members) bound to unique, constant values. Within an enumeration, the members can be compared by identity, and the enumeration itself can be iterated over.  If using Python 3 there is built-in support for unique values, multiple values, auto-numbering, and suspension of aliasing (members with the same value are not identical), plus the ability to have values automatically bound to attributes.

A NamedTuple is a class-based, fixed-length tuple with a name for each possible position accessible using attribute-access notation as well as the standard index notation.

A NamedConstant is a class whose members cannot be rebound; it lacks all other Enum capabilities, however; consequently, it can have duplicate values.

Utility functions include:

- skip: class that prevents attributes from being converted to a
        constant or enum member

- module: inserts NamedConstant and Enum classes into sys.modules
          where it will appear to be a module whose top-level names
          cannot be rebound

- extend_enum: add new members to enumerations after creation

- enum: helper class for creating members with keywords

- constant: helper class for creating constant members
'''

data = dict(
       name='aenum',
       version='1.4.5',
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
            ],
    )

py2_only = ()
py3_only = ('aenum/test_v3.py', )
make = [
        'rst2pdf aenum/doc/aenum.rst --output=aenum/doc/aenum.pdf',
        ]

if __name__ == '__main__':
    if 'install' in sys.argv:
        import os, sys, shutil
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
