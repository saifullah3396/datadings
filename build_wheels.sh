#!/usr/bin/env bash
set -e -x

# Install native dependencies
# yum install ...
/opt/python/cp36-cp36m/bin/pip install six

# Compile wheels
/opt/python/cp36-cp36m/bin/python setup.py bdist_wheel --dist-dir=.
rm -rf build dist datadings.egg-info

# Turn normal wheels into manylinux wheels:
#   - Bundle external shared libraries into the wheels
#for whl in *.whl; do
#    auditwheel repair "${whl}" -w .
#    rm "${whl}"
#done
