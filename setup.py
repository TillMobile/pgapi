import imp
import io
import os
from os import path

import sys

from setuptools import Extension, find_packages, setup

MYDIR = path.abspath(os.path.dirname(__file__))

VERSION = imp.load_source('version', path.join('.', 'httpsql', 'version.py'))
VERSION = VERSION.__version__

REQUIRES = [
  "Cython==0.24",
  "psycopg2==2.6.1",
  "falcon==0.3.0",
  "python-mimeparse==1.5.2",
  "six==1.10.0",
  "requests==2.10.0",
  "gunicorn==19.6.0"
]

cmdclass = {}
ext_modules = []

setup(
    name='httpsql',
    version=VERSION,
    description='PostgreSQL DB to RESTFul API in seconds flat',
    long_description=io.open('README.md', 'r', encoding='utf-8').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Database :: Front-Ends',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='web api rest http cloud db postgresql',
    url='https://github.com/TillMobile/httpsql',
    license='Mozilla Public License Version 2.0',
    packages=find_packages(exclude=('test', )),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    setup_requires=[],
    cmdclass=cmdclass,
    ext_modules=ext_modules
)
