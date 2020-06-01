#!/usr/bin/env bash
set -e -x

# make wheel with Python 3.8
/opt/python/cp38-cp38/bin/python setup.py bdist_wheel
rm -rf build dist datadings.egg-info
