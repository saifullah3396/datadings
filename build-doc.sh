#!/bin/bash
set -e -x

cd doc
rm -rf out source/generated
python -m sphinx -b html source out
rm -rf out/.doctrees
cd ..
