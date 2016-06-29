#!/usr/bin/env python3
from distutils.core import setup

from store import name, version

setup(
    name=name,
    version=version,
    description='a REST storage service',
    license='MIT',
    author='Foster McLane',
    author_email='fkmclane@gmail.com',
    packages=['store'],
)
