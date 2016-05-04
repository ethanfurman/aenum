import setuptools
from distutils.core import setup

long_desc = '''\
`aenum` includes the new Python stdlib enum module available in Python 3.4
backported for previous versions of Python from 2.7 and 3.3+
tested on 2.7, and 3.3+


An `Enum` is a set of symbolic names (members) bound to unique, constant
values.  Within an enumeration, the members can be compared by identity, and
the enumeration itself can be iterated over.

A `NamedTuple` is a class-based, fixed-length tuple with a name for each
possible position accessible using attribute-access notation.

A `NamedConstant` is a class whose members cannot be rebound;  it lacks all other
`Enum` capabilities, however; consequently, it can have duplicate values.
There is also a `module` function that can insert the `NamedConstant` class
into `sys.modules` where it will appear to be a module whose top-level
names cannot be rebound.
'''

data = dict(
       name='aenum',
       version='1.4.1',
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

if __name__ == '__main__':
    setup(**data)
