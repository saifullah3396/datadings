#!/usr/bin/env bash
set -e -x

# Python 2.x and 3.4 are not supported
# remove binaries if still present
rm -rf /opt/python/cp2*
rm -rf /opt/python/cp34*

# make wheel with Python 3.8
/opt/python/cp38-cp38/bin/python setup.py bdist_wheel
