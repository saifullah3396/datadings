#!/usr/bin/env bash
set -e -x

for PYBIN in /opt/python/*/bin/; do
  "${PYBIN}/pip" install -r test-requirements.txt
  "${PYBIN}/pip" install datadings --no-index -f dist
  LIBDIR=$(
    "${PYBIN}/python" -c \
    "import os.path as pt; import datadings; print(pt.dirname(datadings.__file__))"
  )
  (
    cd test
    "${PYBIN}/python" -m pytest -vv
    "${PYBIN}/python" -m pytest --cov="${LIBDIR}" ./* --cov-report term-missing
  )
done
