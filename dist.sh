#!/usr/bin/env bash
set -e
python setup.py bdist_wheel --dist-dir=.
rm -rf build dist datadings.egg-info
