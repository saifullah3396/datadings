#!/usr/bin/env bash
set -e -x

# Python 2.x is not supported
rm -rf /opt/python/cp2*

# make wheel with Python 3.8
/opt/python/cp38-cp38/bin/python setup.py bdist_wheel
