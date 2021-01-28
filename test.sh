#!/usr/bin/env bash
set -e -x

# Python 2.x is not supported
rm -rf /opt/python/cp2*
# Don't test Python 3.5
rm -rf /opt/python/cp35*

for PYBIN in /opt/python/*/bin; do
  (
    cd test
    "${PYBIN}/pip" install -r ../requirements.txt
    "${PYBIN}/pip" install -r ../test-requirements.txt
    "${PYBIN}/pip" install datadings --no-index -f ../dist --no-deps
    LIBDIR=$(
      "${PYBIN}/python" -c \
      "import os.path as pt; import datadings; print(pt.dirname(datadings.__file__))"
    )
    "${PYBIN}/python" -m pytest -vv
    "${PYBIN}/python" -m pytest --cov="${LIBDIR}" ./* --cov-report term-missing
  )
done
