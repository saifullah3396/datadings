#!/usr/bin/env bash

/opt/python/cp36-cp36m/bin/pip install *.whl
/opt/python/cp36-cp36m/bin/pip install pytest
/opt/python/cp36-cp36m/bin/pip install pytest-cov
cd test
LIBDIR=`python -c"import os.path as pt; import datadings; print(pt.dirname(datadings.__file__))"`
pytest --cov=$LIBDIR . --cov-report term-missing
