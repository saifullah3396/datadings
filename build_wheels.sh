#!/usr/bin/env bash
set -e -x

# Compile wheels
/opt/python/${PYVER}/bin/python setup.py bdist_wheel --dist-dir=.
rm -rf build dist datadings.egg-info

# Turn normal wheels into manylinux wheels:
#   - Bundle external shared libraries into the wheels
#for whl in *.whl; do
#    auditwheel repair "${whl}" -w .
#    rm "${whl}"
#done
