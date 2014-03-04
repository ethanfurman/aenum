import sys, os
from distutils.core import setup

long_desc = open('enum/doc/enum.rst').read()

setup( name='enum34',
       version='0.9.23',
       url='https://pypi.python.org/pypi/enum34',
       packages=['enum'],
       package_data={
           'enum' : [
               'LICENSE',
               'README',
               'doc/enum.rst',
               'doc/enum.pdf',
               'test_enum.py',
               ]
           },
       license='BSD License',
       description='Python 3.4 Enum backported to 3.3, 3.2, 3.1, 2.7, 2.6, 2.5, and 2.4',
       long_description=long_desc,
       provides=['enum'],
       author='Ethan Furman',
       author_email='ethan@stoneleaf.us',
       classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Topic :: Software Development' ],
     )

