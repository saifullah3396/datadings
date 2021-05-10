#!/usr/bin/env bash
set -e -x
shopt -s extglob

for PYBIN in /opt/python/@(${PYVERS})*/bin; do
  (
    cd test
    "${PYBIN}/pip" install -r ../requirements.txt
    "${PYBIN}/pip" install --only-binary ":all:" -r ../test-requirements.txt
    "${PYBIN}/pip" install datadings --no-index -f ../dist --no-deps
    LIBDIR=$(
      "${PYBIN}/python" -c \
      "import os.path as pt; import datadings; print(pt.dirname(datadings.__file__))"
    )
    "${PYBIN}/python" -m pytest -vv --cov="${LIBDIR}" ./test_*.py --cov-report term-missing
  )
done
