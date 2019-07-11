#!/usr/bin/env bash
echo "running tests for python version:"
echo "$(/opt/python/*${PYVER}*/bin/python --version)"
/opt/python/*${PYVER}*/bin/pip install *.whl
/opt/python/*${PYVER}*/bin/pip install pytest
/opt/python/*${PYVER}*/bin/pip install pytest-cov
cd test

LIBDIR=`/opt/python/*${PYVER}*/bin/python -c"import os.path as pt; import datadings; print(pt.dirname(datadings.__file__))"`
/opt/python/*${PYVER}*/bin/python -m pytest --cov=$LIBDIR * --cov-report term-missing
