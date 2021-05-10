#!/usr/bin/env bash
set -e -x

# make wheel with Python 3.8
/opt/python/cp39-cp39/bin/python setup.py bdist_wheel
