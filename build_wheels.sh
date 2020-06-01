#!/usr/bin/env bash
set -e -x

# delete Python 2.x
rm -rf /opt/python/cp2*

# make wheel with Python 3.8
/opt/python/cp38-cp38/bin/pip wheel . -v -w dist
rm -rf build dist datadings.egg-info
